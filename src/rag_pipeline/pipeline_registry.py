"""Project pipelines."""

from typing import Dict

from kedro.pipeline import Pipeline

from rag_pipeline.pipelines import collect_data, generate_script


def register_pipelines() -> Dict[str, Pipeline]:
    """Register the project's pipelines.

    Returns:
        A mapping from pipeline names to ``Pipeline`` objects.
    """
    collect_data_pipeline = collect_data.create_pipeline()
    generate_script_pipeline = generate_script.create_pipeline()

    return {
        "collect_data": collect_data_pipeline,
        "generate_script": generate_script_pipeline,
        "__default__": generate_script_pipeline,
    }
