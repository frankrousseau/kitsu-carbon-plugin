from . import resources


routes = [
    ("/factors", resources.CarbonFactorsResource),
    ("/factors/<country_code>", resources.CarbonFactorResource),
    ("/footprint", resources.StudioFootprintResource),
    (
        "/productions/<project_id>/footprint/sequences",
        resources.ProductionSequenceFootprintResource,
    ),
    (
        "/productions/<project_id>/footprint/episodes",
        resources.ProductionEpisodeFootprintResource,
    ),
    (
        "/productions/<project_id>/footprint/assets",
        resources.ProductionAssetFootprintResource,
    ),
    (
        "/productions/<project_id>/footprint/task-types",
        resources.ProductionTaskTypeFootprintResource,
    ),
    (
        "/productions/<project_id>/footprint/summary",
        resources.ProductionFootprintSummaryResource,
    ),
]


def post_install(manifest):
    """
    Seed initial carbon factor data for 23 countries.
    """
    from .models import CarbonFactor

    CarbonFactor.seed_initial_data()
