# Ruby — Gemfile or *.gemspec

## Detect

`Gemfile` or a `*.gemspec` file, per top-level package directory.

Match: stack

## Item gate

From that directory, run `bundle check` to confirm dependencies are installed. If
`bundle exec rake -AT` lists an exact `rake test` task, use `bundle exec rake test`;
otherwise use `bundle exec rspec` when the bundle includes rspec. Add
`bundle exec rubocop` when the bundle includes rubocop.

## Site inspection

The project's documented CI task when one exists. Otherwise `simplecov` coverage when
the bundle includes it, and a `brakeman` security sweep for Rails apps.

## Notes

Use the project's Ruby and Bundler versions. If neither a Rake test task nor rspec is
present, use the test command documented by the project. Missing dependencies or a
missing test command are setup gaps.
