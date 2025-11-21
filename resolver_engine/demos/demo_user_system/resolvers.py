from ...core.resolver_base import BaseResolver, ResolverSpec, ResolverOutput
from ...core.state import ResolutionContext
from .schemas import DemoFacts


registered = False


def register_demo_resolvers():
    global registered
    if registered:
        return

    @BaseResolver.register(
        ResolverSpec(
            name="UserIdResolver",
            description="Derive user id from name",
            input_facts={DemoFacts.USER_NAME},
            output_facts={DemoFacts.USER_ID},
            impact={DemoFacts.USER_ID: 1.0},
        )
    )
    class UserIdResolver(BaseResolver):
        def run(self, ctx: ResolutionContext):
            base = ctx.state[DemoFacts.USER_NAME].value
            return [ResolverOutput(DemoFacts.USER_ID, len(str(base)))]

    @BaseResolver.register(
        ResolverSpec(
            name="FavoriteColorResolver",
            description="Assign favorite color",
            input_facts={DemoFacts.USER_ID},
            output_facts={DemoFacts.FAVORITE_COLOR},
            impact={DemoFacts.FAVORITE_COLOR: 0.5},
        )
    )
    class FavoriteColorResolver(BaseResolver):
        def run(self, ctx: ResolutionContext):
            uid = ctx.state[DemoFacts.USER_ID].value
            color = "blue" if uid % 2 == 0 else "green"
            return [ResolverOutput(DemoFacts.FAVORITE_COLOR, color)]

    registered = True
