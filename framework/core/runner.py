from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm


class PipelineRunner:
    @staticmethod
    def _flush_ordered_results(completed_results, next_idx, flush_callback):
        while next_idx in completed_results:
            flush_callback(completed_results.pop(next_idx))
            next_idx += 1
        return next_idx

    def run_stage(self, stage, context):
        stage.prepare(context)
        indices = list(stage.get_indices(context))
        completed_results = {}
        next_idx = indices[0] if indices else None

        with ThreadPoolExecutor(max_workers=stage.max_workers(context)) as executor:
            future_to_idx = {executor.submit(stage.process_row, idx, context): idx for idx in indices}
            for future in tqdm(as_completed(future_to_idx), total=len(future_to_idx), desc=f"running {stage.name} ..."):
                result = future.result()
                completed_results[result["idx"]] = result
                if next_idx is not None:
                    next_idx = self._flush_ordered_results(
                        completed_results=completed_results,
                        next_idx=next_idx,
                        flush_callback=lambda ordered_result: stage.flush_result(ordered_result, context)
                    )

        stage.finalize(context)

    def run(self, experiment):
        context = experiment.build_context()
        experiment.setup(context)
        for stage in experiment.build_stages():
            self.run_stage(stage, context)
        experiment.teardown(context)
        return context

