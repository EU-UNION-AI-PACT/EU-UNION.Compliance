# EU-UNION Compliance

## Netlify deployment

The repository's `netlify.toml` explicitly runs
`yarn install --frozen-lockfile --production=false` before `yarn build` from
`frontend`, then publishes `frontend/build`. This installs the development
dependencies, including the CRACO build tool, even when a CLI deployment skips
automatic dependency installation or uses a production environment.
When changing dependency versions or resolutions in `frontend/package.json`,
run `yarn install --ignore-scripts --production=false` from `frontend` and include
the updated `frontend/yarn.lock` with the change. Deployments use the frozen
lockfile to prevent dependency resolution from changing during a build.
Deploy the compiled
output, not the repository root or `frontend/public`, which contains only the
HTML template.

The fallback rewrite serves `index.html` for client-side routes such as `/paper`
and `/compliance`, allowing direct links and browser refreshes to reach React
Router. Existing static files are served normally.

This configuration deploys the React frontend only. The Python backend must be
hosted separately, with `REACT_APP_BACKEND_URL` configured in Netlify's build
environment to point to that service. Do not store credentials in the repository.

After deployment, check the homepage and directly open or refresh `/compliance`
to verify both the published output and client-side routing.
