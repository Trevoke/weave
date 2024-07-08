import asyncio

import pytest

import weave
from weave import Dataset, Evaluation, Model, ref_base
from weave.flow.scorer import MultiTaskBinaryClassificationF1

pytestmark = pytest.mark.webtest


dataset_rows = [{"input": "1 + 2", "target": 3}, {"input": "2**4", "target": 15}]
dataset = Dataset(rows=dataset_rows)


expected_eval_result = {
    "model_output": {
        "mean": 9.5,
        "none_fraction": 0.0,
    },
    "score": {
        "true_count": 1,
        "true_fraction": 0.5,
        "none_fraction": 0.0,
    },
    "model_latency": {
        "mean": pytest.approx(0, abs=0.05),
        "none_fraction": 0.0,
    },
}


class EvalModel(Model):
    @weave.op()
    async def predict(self, input) -> str:
        return eval(input)


@weave.op()
def score(target, model_output):
    return target == model_output


@weave.op()
def example_to_model_input(example):
    return {"input": example["input"]}


def test_evaluate_callable_as_model(client):
    @weave.op()
    async def model_predict(input) -> str:
        return eval(input)

    evaluation = Evaluation(
        dataset=dataset_rows,
        scorers=[score],
    )
    result = asyncio.run(evaluation.evaluate(model_predict))
    assert result == expected_eval_result


def test_predict_can_receive_other_params(client):
    @weave.op()
    async def model_predict(input, target) -> str:
        return eval(input) + target

    evaluation = Evaluation(
        dataset=dataset_rows,
        scorers=[score],
    )
    result = asyncio.run(evaluation.evaluate(model_predict))
    assert result == {
        "model_output": {
            "mean": 18.5,
            "none_fraction": 0.0,
        },
        "score": {
            "true_count": 0,
            "true_fraction": 0.0,
            "none_fraction": 0.0,
        },
        "model_latency": {
            "mean": pytest.approx(0, abs=0.05),
            "none_fraction": 0.0,
        },
    }


def test_can_preprocess_model_input(client):
    @weave.op()
    async def model_predict(x) -> str:
        return eval(x)

    @weave.op()
    def preprocess(example):
        return {"x": example["input"]}

    evaluation = Evaluation(
        dataset=dataset_rows,
        scorers=[score],
        preprocess_model_input=preprocess,
    )
    result = asyncio.run(evaluation.evaluate(model_predict))
    assert result == expected_eval_result


def test_evaluate_rows_only(client):
    evaluation = Evaluation(
        dataset=dataset_rows,
        scorers=[score],
    )
    model = EvalModel()
    result = asyncio.run(evaluation.evaluate(model))
    assert result == expected_eval_result


def test_evaluate_other_model_method_names(eager_mode):
    class EvalModel(Model):
        @weave.op()
        async def infer(self, input) -> str:
            return eval(input)

    evaluation = Evaluation(
        dataset=dataset_rows,
        scorers=[score],
    )
    model = EvalModel()
    result = asyncio.run(evaluation.evaluate(model))
    assert result == expected_eval_result


def test_score_as_class(client):
    class MyScorer(weave.Scorer):
        @weave.op()
        def score(self, target, model_output):
            return target == model_output

    evaluation = Evaluation(
        dataset=dataset_rows,
        scorers=[MyScorer()],
    )
    model = EvalModel()
    result = asyncio.run(evaluation.evaluate(model))
    assert result == {
        "model_output": {
            "mean": 9.5,
            "none_fraction": 0.0,
        },
        "MyScorer": {
            "true_count": 1,
            "true_fraction": 0.5,
            "none_fraction": 0.0,
        },
        "model_latency": {
            "mean": pytest.approx(0, abs=0.05),
            "none_fraction": 0.0,
        },
    }


def test_score_with_custom_summarize(client):
    class MyScorer(weave.Scorer):
        @weave.op()
        def summarize(self, score_rows):
            assert list(score_rows) == [True, False]
            return {"awesome": 3}

        @weave.op()
        def score(self, target, model_output):
            return target == model_output

    evaluation = Evaluation(
        dataset=dataset_rows,
        scorers=[MyScorer()],
    )
    model = EvalModel()
    result = asyncio.run(evaluation.evaluate(model))
    assert result == {
        "model_output": {
            "mean": 9.5,
            "none_fraction": 0.0,
        },
        "MyScorer": {"awesome": 3},
        "model_latency": {
            "mean": pytest.approx(0, abs=0.05),
            "none_fraction": 0.0,
        },
    }


def test_multiclass_f1_score(client):
    evaluation = Evaluation(
        dataset=[{"target": {"a": False, "b": True}, "pred": {"a": True, "b": False}}],
        scorers=[MultiTaskBinaryClassificationF1(class_names=["a", "b"])],
    )

    @weave.op()
    def return_pred(pred):
        return pred

    result = asyncio.run(evaluation.evaluate(return_pred))
    assert result == {
        "model_output": {
            "a": {
                "true_count": 1,
                "true_fraction": 1.0,
                "none_fraction": 0.0,
            },
            "b": {
                "true_count": 0,
                "true_fraction": 0.0,
                "none_fraction": 0.0,
            },
        },
        "MultiTaskBinaryClassificationF1": {
            "a": {"f1": 0, "precision": 0.0, "recall": 0},
            "b": {"f1": 0, "precision": 0, "recall": 0.0},
        },
        "model_latency": {
            "mean": pytest.approx(0, abs=0.05),
            "none_fraction": 0.0,
        },
    }


def test_score_with_errors(client):
    @weave.op
    def raise_above_2_score(model_output: int, actual: int) -> dict:
        if actual > 2:
            raise ValueError("actual is too big")
        return {"actual": model_output == actual}

    evaluation = Evaluation(
        dataset=[
            {"pred": 1, "actual": 1},
            {"pred": 2, "actual": 2},
            {"pred": 3, "actual": 3},
            {"pred": 4, "actual": 4},
        ],
        scorers=[raise_above_2_score],
    )

    @weave.op()
    def return_pred(pred):
        return pred

    result = asyncio.run(evaluation.evaluate(return_pred))

    assert result == {
        "model_output": {
            "mean": 2.5,
            "none_fraction": 0.0,
        },
        "raise_above_2_score": {
            "actual": {
                "true_count": 2,
                "true_fraction": 0.5,
                "none_fraction": 0.5,  # for cases 3,4 which raise because they are > 2
            }
        },
        "model_latency": {
            "mean": pytest.approx(0, abs=0.1),
            "none_fraction": 0.0,
        },
    }
