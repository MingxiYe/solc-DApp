#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys
sys.path.append("./utils")
import utils

if __name__ == "__main__":
    inputDir, outputDir, contractName, graph = parseArg(sys.argv[1:])

    ## print uml graph in outputDir
    if graph:
        parseDependency(inputDir, outputDir, graph)
        sys.exit(0)

    ## complie ${contractName}
    compileContract(inputDir, outputDir, contractName)
