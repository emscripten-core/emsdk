"""Defines a provider and rule for platform information.
"""

PlatformInfo = provider(
    doc = "Provides some info about a platform",
    fields = {
        "script_extension": "The script extension for the platform, e.g. 'sh' or 'bat'",
    },
)

platform_info = rule(
    implementation = lambda ctx: PlatformInfo(
        script_extension = ctx.attr.script_extension,
    ),
    attrs = {
        "script_extension": attr.string(
            mandatory = True,
            values = ["sh", "bat"],
            doc = "The script extension for the platform, e.g. 'sh' or 'bat'",
        ),
    },
)
