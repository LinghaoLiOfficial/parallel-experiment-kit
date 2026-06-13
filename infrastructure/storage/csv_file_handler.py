from pathlib import Path

import pandas as pd

from infrastructure.base.result import Result
from infrastructure.logging.logger import get_logger
from infrastructure.storage.json_file_handler import JsonFileHandler
from infrastructure.utils.time_utils import TimeParser


logger = get_logger(__name__)


class CSVFileHandler:
    def __init__(self, save_path: str, write_mode="w", checkpoint_rows=0, max_rows_per_file=None, resume=False):
        self.write_mode = write_mode
        self.save_path = Path(save_path)
        self.file_info_path = self.save_path.with_suffix(".json")
        self.checkpoint_rows = checkpoint_rows
        self.max_rows_per_file = max_rows_per_file
        self.resume = resume

        self.latest_part_num = 1
        self.cursor_path = self.init_cursor_path()
        self.waiting_data_list = []
        self.recorded_num = 0
        self.processed_num = 0

        self.start_time = TimeParser.get_current_time()
        self.duration_for_seconds = 0

        self.init_file_info()

    def init_cursor_path(self):
        if self.write_mode == "a":
            return self.save_path.with_name(f"{self.save_path.stem}_part_1{self.save_path.suffix}")
        return self.save_path

    def init_file_info(self):
        if self.resume:
            if self.file_info_path.exists():
                try:
                    json_read_result = JsonFileHandler.read(self.file_info_path)
                    loaded_file_info = json_read_result.get_data_on_results()
                    self.write_mode = loaded_file_info["write_mode"]
                    self.save_path = Path(loaded_file_info["save_path"])
                    self.file_info_path = Path(loaded_file_info["file_info_path"])
                    self.latest_part_num = loaded_file_info["latest_part_num"]
                    self.cursor_path = Path(loaded_file_info["cursor_path"])
                    self.processed_num = loaded_file_info["processed_num"]
                    self.recorded_num = loaded_file_info["recorded_num"]
                    self.duration_for_seconds = loaded_file_info["duration_for_seconds"]
                    logger.info(
                        f"从断点恢复: self.cursor_path={self.cursor_path}, "
                        f"self.processed_num={self.processed_num}, self.recorded_num={self.recorded_num}"
                    )
                except Exception as exc:
                    logger.warning(f"加载元数据失败: {exc}，从头开始")
                    self.clean_existing_files()
            else:
                logger.info("未找到元数据文件，从头开始")
                self.clean_existing_files()
        else:
            self.clean_existing_files()
            logger.info(f"不启用断点续传，已清空相关文件，从头开始: {self.save_path}")

    def clean_existing_files(self):
        if self.save_path.exists():
            self.save_path.unlink()

        for part_file in self.save_path.parent.glob(f"{self.save_path.stem}_part_?{self.save_path.suffix}"):
            try:
                part_file.unlink()
            except Exception as exc:
                logger.warning(f"删除part文件失败 {part_file}: {exc}")

        if self.file_info_path.exists():
            try:
                self.file_info_path.unlink()
            except Exception as exc:
                logger.warning(f"删除元文件数据文件失败: {exc}")

        self.latest_part_num = 1
        self.cursor_path = self.init_cursor_path()
        self.waiting_data_list = []
        self.recorded_num = 0
        self.processed_num = 0

    def save(self, data=None):
        try:
            if self.write_mode == "w":
                pd.DataFrame(data).to_csv(str(self.cursor_path), index=False)
                self.recorded_num = len(data) if data is not None else 0
                self.processed_num = self.recorded_num
            elif self.write_mode == "a":
                if data is None:
                    self.cache_data()
                else:
                    self.waiting_data_list.append(data)
                    self.recorded_num += 1
                    if (
                        self.max_rows_per_file is not None
                        and self.recorded_num >= self.max_rows_per_file
                        and self.recorded_num % self.max_rows_per_file == 0
                    ):
                        self.cache_data()
                        self.latest_part_num = (self.recorded_num // self.max_rows_per_file) + 1
                        self.cursor_path = Path(
                            f"{self.save_path.parent}/{self.save_path.stem}_part_{self.latest_part_num}{self.save_path.suffix}"
                        )
                    if len(self.waiting_data_list) >= self.checkpoint_rows:
                        self.cache_data()
        except Exception as exc:
            logger.warning(f"CSVFileHandler common_save error, e={exc}")
            return Result.build_error()

        return Result.build_success()

    def _get_part_row_count(self, file_path: Path):
        if not file_path.is_file():
            return 0
        try:
            return len(pd.read_csv(str(file_path)))
        except pd.errors.EmptyDataError:
            return 0

    def _move_to_next_part(self):
        self.latest_part_num += 1
        self.cursor_path = self.save_path.with_name(f"{self.save_path.stem}_part_{self.latest_part_num}{self.save_path.suffix}")

    def _ensure_cursor_points_to_writable_part(self):
        if self.max_rows_per_file is None:
            return
        while self._get_part_row_count(self.cursor_path) >= self.max_rows_per_file:
            self._move_to_next_part()

    @staticmethod
    def _append_dataframe(file_path: Path, new_df: pd.DataFrame):
        if file_path.is_file():
            try:
                existing_df = pd.read_csv(str(file_path))
                existing_columns = list(existing_df.columns)
                new_columns = list(new_df.columns)

                if set(existing_columns) != set(new_columns):
                    all_columns_sorted = existing_columns.copy()
                    for col in new_columns:
                        if col not in existing_columns:
                            all_columns_sorted.append(col)
                    existing_df = existing_df.reindex(columns=all_columns_sorted)
                    new_df = new_df.reindex(columns=all_columns_sorted)
                    pd.concat([existing_df, new_df], ignore_index=True).to_csv(str(file_path), index=False, mode="w")
                else:
                    new_df = new_df.reindex(columns=existing_columns)
                    new_df.to_csv(str(file_path), index=False, mode="a", header=False)
            except pd.errors.EmptyDataError:
                new_df.to_csv(str(file_path), index=False, mode="w")
        else:
            new_df.to_csv(str(file_path), index=False, mode="w")

    def cache_data(self):
        if len(self.waiting_data_list) == 0:
            return

        try:
            pending_data_list = self.waiting_data_list
            total_cached_num = 0

            while len(pending_data_list) > 0:
                self._ensure_cursor_points_to_writable_part()
                if self.max_rows_per_file is None:
                    chunk_data_list = pending_data_list
                    pending_data_list = []
                else:
                    current_rows = self._get_part_row_count(self.cursor_path)
                    remaining_capacity = self.max_rows_per_file - current_rows
                    if remaining_capacity <= 0:
                        self._move_to_next_part()
                        continue
                    chunk_data_list = pending_data_list[:remaining_capacity]
                    pending_data_list = pending_data_list[remaining_capacity:]

                new_df = pd.DataFrame(chunk_data_list)
                self._append_dataframe(self.cursor_path, new_df)
                total_cached_num += len(chunk_data_list)

            self.processed_num += total_cached_num
            self.waiting_data_list = []
            duration_for_seconds = self.duration_for_seconds + TimeParser.calculate_duration_for_seconds(self.start_time)
            JsonFileHandler.save(
                file_path=self.file_info_path,
                data={
                    "write_mode": self.write_mode,
                    "save_path": str(self.save_path),
                    "file_info_path": str(self.file_info_path),
                    "latest_part_num": self.latest_part_num,
                    "cursor_path": str(self.cursor_path),
                    "processed_num": self.processed_num,
                    "recorded_num": self.processed_num,
                    "duration": str(TimeParser.calculate_duration(duration_for_seconds)),
                    "duration_for_seconds": duration_for_seconds,
                },
            )
        except Exception as exc:
            logger.warning(f"缓存数据失败, e={exc}")

    def read(self):
        if self.write_mode == "w":
            try:
                return pd.read_csv(self.save_path, encoding="utf-8")
            except pd.errors.EmptyDataError:
                return pd.DataFrame()

        if self.write_mode == "a":
            part_df_list = []
            for i in range(1, self.latest_part_num + 1):
                part_file = f"{self.save_path.parent}/{self.save_path.stem}_part_{i}{self.save_path.suffix}"
                try:
                    part_df_list.append(pd.read_csv(part_file, encoding="utf-8"))
                except pd.errors.EmptyDataError:
                    logger.warning(f"Warning: Part file {part_file} is empty, skipping.")
                except FileNotFoundError:
                    logger.warning(f"Warning: Part file {part_file} not found, skipping.")
            if part_df_list:
                return pd.concat(part_df_list, axis=0, ignore_index=True)
        return pd.DataFrame()
