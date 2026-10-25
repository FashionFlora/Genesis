"""Tests for between-life evolutionary reporting."""

from evolve import _generation_progress


def test_generation_progress_is_separate_from_single_life_results():
    initial = _generation_progress(0.25, 0.5, 0.25, 0.5)
    later = _generation_progress(0.75, 1.0, 0.25, 0.5)

    assert initial == {"fitness_mean_from_initial": 0.0,
                       "score_best_from_initial": 0.0}
    assert later == {"fitness_mean_from_initial": 0.5,
                     "score_best_from_initial": 0.5}
