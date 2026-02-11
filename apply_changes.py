#!/usr/bin/env python3
"""Script to apply changes to main.py."""

with open('/home/rogermt/forgesyte/server/app/main.py', 'r') as f:
    content = f.read()

# Add import after execution_router import
if 'from .routes_pipeline import init_pipeline_routes' not in content:
    content = content.replace(
        'from .api_routes.routes.execution import router as execution_router',
        'from .api_routes.routes.execution import router as execution_router\nfrom .routes_pipeline import init_pipeline_routes'
    )

# Add router registration after execution_router
if 'app.include_router(init_pipeline_routes())' not in content:
    content = content.replace(
        '    app.include_router(execution_router)',
        '    app.include_router(execution_router)\n    app.include_router(init_pipeline_routes())'
    )

with open('/home/rogermt/forgesyte/server/app/main.py', 'w') as f:
    f.write(content)

print('Changes applied successfully')

