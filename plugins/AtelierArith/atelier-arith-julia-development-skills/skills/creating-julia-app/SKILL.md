---
name: creating-julia-app
description: Use when you create a CLI written in Julia packages or MCP servers
---

# Creating a Julia app

Apps are Julia packages that are intended to be run as "standalone programs" (by e.g. typing the name of the app in the terminal possibly together with some arguments or flags/options). This is in contrast to most Julia packages that are used as "libraries" and are loaded by other files or in the Julia REPL.

A Julia app is structured similar to a standard Julia library with the following additions:

A `@main` entry point in the package module (see the Julia help on `@main` for details)
An `[apps]` section in the `Project.toml` file listing the executable names that the package provides.
A very simple example of an app that prints the reversed input arguments would be:

```julia
# src/MyReverseApp.jl
module MyReverseApp

function (@main)(ARGS)
    for arg in ARGS
        print(stdout, reverse(arg), " ")
    end
    return
end

end # module
```

```toml
# Project.toml

# standard fields here

[apps]
reverse = {}
```

The empty table `{}` is to allow for giving metadata about the app.

After installing this app one could run:

```
$ ~/.julia/bin/reverse some input string
 emos tupni gnirts
```

directly in the terminal. See the following link to learn more:

- [Multiple Apps per Package](https://pkgdocs.julialang.org/v1/apps/#Multiple-Apps-per-Package)
