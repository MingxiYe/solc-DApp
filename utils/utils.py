import getopt
import os, json, re
from solidity_parser import parser
from graphviz import Digraph
import time

'''
parse arguments from cmd input
'''
def parseArg(argv):
    inputDir = ""
    outputDir = "./output"
    contractName = ""
    graph = False
    try:
        opts, args = getopt.getopt(argv, "hgi:o:n:", ["help", "graph", "inputDir=", "outputDir=", "contractName="])
    except getopt.GetoptError:
        print("python3 main.py -i <inputDir> -o <outputDir> -n <contractName>")
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print("python3 main.py -i <inputDir> -o <outputDir> -n <contractName>")
            sys.exit()
        elif opt in ("-g", "--graph"):
            graph = True
        elif opt in ("-i", "--inputDir"):
            inputDir = arg
        elif opt in ("-o", "--outputDir"):
            outputDir = arg
        elif opt in ("-n", "--contractName"):
            contractName = arg
    if inputDir == "" or (contractName == "" and graph == False):
        print("python3 main.py -i <inputDir> -o <outputDir> -n <contractName>")
        sys.exit(2)
    elif not os.path.isdir(inputDir):
        print(inputDir, "is not a input dir")
        sys.exit(2)
    elif not os.path.isdir(outputDir):
        print(outputDir, "is not a output dir")
        sys.exit(2)
    elif contractName != "" and not os.path.exists(os.path.join(inputDir, contractName + ".sol")):
        print("contract", contractName, "do not exist")
        sys.exit(2)
    return inputDir, outputDir, contractName, graph

'''
parse solidity version by readline
'''
def parseVersionReadline(filePath):
    f = open(filePath)
    line = f.readline()
    while line:
        if re.search('pragma', line) != None and re.search('0\.[0-9\.]*', line) != None:
            return re.search('0\.[0-9\.]*', line).group(0)
        line = f.readline()
    f.close()
    return "unknown version"

'''
parse solidity version from .sol file
'''
def parseVersion(filePath):
    try:
        fileUnits = parser.parse_file(filePath, loc=False)
    except Exception as e:
        return parseVersionReadline(filePath)
    for item in fileUnits["children"]:
        if item["type"] == "PragmaDirective":
            return item["value"]
    return "unknown version"

'''
switch solc version by solc-select
'''
def switchVersion(version):
    cleanVersion = re.search('0\.[0-9\.]*', version).group(0)
    # os.system("solc-select install " + cleanVersion)
    os.system("solc-select use " + cleanVersion)
    time.sleep(5)

'''
parse contract list with absolute path
'''
def parseContractList(inputDir):
    result = dict()
    inputFiles = os.listdir(inputDir)
    for inputFile in inputFiles:
        targetPath = os.path.join(inputDir, inputFile)
        targetPath = os.path.abspath(targetPath)
        if (not os.path.isdir(targetPath)) \
                and re.match("[\S]*.sol$", inputFile) != None:
            result[targetPath] = inputFile
        elif os.path.isdir(targetPath):
            nestResult = parseContractList(targetPath)
            for key, value in nestResult.items():
                result[key] = value
    return result

'''
parse import file list in relative path
'''
def parseImportList(filePath):
    try:
        fileUnits = parser.parse_file(filePath, loc=False)
    except Exception as e:
        return []
    result = []
    try:
        for item in fileUnits["children"]:
            if item["type"] == "ImportDirective":
                result.append(item["path"])
    except Exception as e:
        print(filePath)
        # print(fileUnits)
    return result

'''
draw dependency graph
'''
def parseDependency(inputDir, outputDir, graph):
    result = parseContractList(inputDir)
    dot = Digraph(comment="The Dependency Graph", node_attr={'shape': 'record'})
    ## add node from the contract list
    for path, name in result.items():
        dot.node(name = path, label = "{%s|path: %s|version: %s}"%(name, path, parseVersion(path)))
    ## add graph from the import list
    for path, name in result.items():
        importFiles = parseImportList(path)
        dirName = os.path.dirname(path)
        for importFile in importFiles:
            realPath = os.path.join(dirName, importFile)
            for key in result.keys():
                if os.path.exists(realPath) and os.path.samefile(key, realPath):
                    realPath = key
                    break
            if realPath in result:
                dot.edge(realPath, path)
            else:
                dot.node(name = realPath, label = "{404|path: %s}"%realPath)
                dot.edge(realPath, path)
    if graph:
        dot.render(os.path.join(outputDir, "DependencyGraph.gv"), format='png', view=True)
    return dot

'''
get leaf node of dependency graph
'''
def getLeafNode(inputDir):
    result = parseContractList(inputDir)
    nodeList = dict()
    ## add node from the contract list
    for path, name in result.items():
        nodeList[path] = 0
    ## calculate out degree of each node
    for path, name in result.items():
        importFiles = parseImportList(path)
        dirName = os.path.dirname(path)
        for importFile in importFiles:
            realPath = os.path.join(dirName, importFile)
            for key in result.keys():
                if os.path.exists(realPath) and os.path.samefile(key, realPath):
                    realPath = key
                    break
            if realPath in result:
                nodeList[realPath] += 1
    return nodeList                

'''
compile DApp
'''
def compileDapp(inputDir, outputDir):
    ## get leaf node (contract)
    nodeList = getLeafNode(inputDir)
    leafNodes = []
    for path, outDegree in nodeList.items():
        if outDegree == 0:
            leafNodes.append(path)
    ## compile leaf node
    for leafNode in leafNodes:
        (_, contractName) = os.path.split(leafNode)
        targetPath = os.path.join(outputDir, contractName[:len(contractName) - 4] + ".json")
        if os.path.exists(targetPath) and os.path.getsize(targetPath):
            continue
        version = parseVersion(leafNode)
        if version == "unknown version":
            print("unable to identify solidity version of", contractName)
            continue
        switchVersion(version)
        basePath = os.path.join(os.path.dirname(inputDir), "node_modules")
        if not os.path.exists(basePath):
            os.mkdir(basePath)
        _, _, importLibs = calculateImportLib(inputDir)
        compileCommand = "solc --combined-json abi,bin,bin-runtime,srcmap,srcmap-runtime,ast "
        for importLib in importLibs:
            libs = importLib.split("/")
            if libs[0] == ".":
                continue
            compileCommand = compileCommand + libs[0] + "=" + os.path.join(basePath, libs[0]) + " "
        compileCommand = compileCommand \
                    + leafNode + " > " \
                    + targetPath \
                    + " --allow-paths " \
                    + os.path.dirname(inputDir)
        os.system(compileCommand)

'''
compile contract
'''
def compileContract(inputDir, outputDir, targetContract):
    ## get leaf node (contract)
    nodeList = getLeafNode(inputDir)
    leafNode = ""
    for path, outDegree in nodeList.items():
        (cPath, cName) = os.path.split(path)
        cName = cName[:len(cName) - 4]
        if cName == targetContract:
            leafNode = path
    # compile leaf node
    if leafNode == "":
        return
    (_, contractName) = os.path.split(leafNode)
    targetPath = os.path.join(outputDir, contractName[:len(contractName) - 4] + ".json")
    version = parseVersion(leafNode)
    if version == "unknown version":
        print("unable to identify solidity version of", contractName)
        return
    switchVersion(version)
    basePath = os.path.join(os.path.dirname(inputDir), "node_modules")
    if not os.path.exists(basePath):
        os.mkdir(basePath)
    _, _, importLibs = calculateImportLib(inputDir)
    compileCommand = "solc --combined-json abi,bin,bin-runtime,srcmap,srcmap-runtime,ast "
    for importLib in importLibs:
        libs = importLib.split("/")
        if libs[0] == ".":
            continue
        compileCommand = compileCommand + libs[0] + "=" + os.path.join(basePath, libs[0]) + " "
    compileCommand = compileCommand \
                + leafNode + " > " \
                + targetPath \
                + " --allow-paths " \
                + os.path.dirname(inputDir)
    os.system(compileCommand)

'''
calculate how many import lib
'''
def calculateImportLib(inputDir):
    ## get all node (contract)
    result = parseContractList(inputDir)
    modulePath = os.path.dirname(inputDir)
    modulePath = os.path.join(modulePath, "node_modules")
    ## calculate import lib
    libNum = 0
    lib = []
    for path, name in result.items():
        importFiles = parseImportList(path)
        flag = False
        for importFile in importFiles:
            importFile = importFile.replace("'", "")
            dirName = os.path.dirname(path)
            if not os.path.exists(os.path.join(dirName, importFile)):
                    # and not os.path.exists(os.path.join(modulePath, importFile)):
                flag = True
                # print(os.path.join(modulePath, importFile))
                # print(os.path.join(dirName, importFile))
                lib.append(importFile)
        if flag:
            libNum += 1
    return libNum, len(result.keys()), list(set(lib))

'''
get contract string without ''pragma solidity''
'''
def getPackedContract(contractPath, nodeModulePath):
    f = open(contractPath, 'r')
    contractStringWithVersion = f.read()
    f.close()
    versionPattern = 'pragma solidity [\S]*;'
    versionString = re.search(versionPattern, contractStringWithVersion)
    if versionString == None:
        return "failed", "failed"
    versionString = versionString.group()
    contractStringWithoutVersion = re.sub(versionPattern, '', contractStringWithVersion)

    result = ""

    importPattern1 = 'import[\s]*([\S]*);'
    importItem = re.search(importPattern1, contractStringWithoutVersion)
    while importItem != None:
        contractStringWithoutVersion = re.sub(importPattern1, '', contractStringWithoutVersion)
        targetPath1 = os.path.join(contractPath, importItem.group(1))
        targetPath2 = os.path.join(nodeModulePath, importItem.group(1))
        importItem = re.search(importPattern1, contractStringWithoutVersion)
        if os.path.exists(targetPath1):
            tempVersion, tempresult =  getPackedContract(targetPath1, nodeModulePath)
            if tempVersion == "failed":
                return "failed", "failed"
            result = result + tempresult
        elif os.path.exists(targetPath2):
            tempVersion, tempresult =  getPackedContract(targetPath2, nodeModulePath)
            if tempVersion == "failed":
                return "failed", "failed"
            result = result + tempresult
        else:
            return "failed", "failed"

    importPattern2 = 'import[\s]*[\S]*[\s]*from[\s]*([\S]*);'
    importItem = re.search(importPattern2, contractStringWithoutVersion)
    result = ""
    while importItem != None:
        contractStringWithoutVersion = re.sub(importPattern2, '', contractStringWithoutVersion)
        targetPath1 = os.path.join(contractPath, importItem.group(1))
        targetPath2 = os.path.join(nodeModulePath, importItem.group(1))
        importItem = re.search(importPattern2, contractStringWithoutVersion)
        if os.path.exists(targetPath1):
            tempVersion, tempresult =  getPackedContract(targetPath1, nodeModulePath)
            if tempVersion == "failed":
                return "failed", "failed"
            result = result + tempresult
        elif os.path.exists(targetPath2):
            tempVersion, tempresult =  getPackedContract(targetPath2, nodeModulePath)
            if tempVersion == "failed":
                return "failed", "failed"
            result = result + tempresult
        else:
            return "failed", "failed"

    result = result + contractStringWithoutVersion
    return versionString, result


'''
get packed leaf contracts
'''
def getPacked(inputDir, outputDir):
    ## get node_modules path
    nodeModulePath = os.path.join(os.path.dirname(inputDir), "node_modules")
    ## get leaf node (contract)
    nodeList = getLeafNode(inputDir)
    leafNodes = []
    for path, outDegree in nodeList.items():
        # if outDegree == 0:
        leafNodes.append(path)
    ## compile leaf node
    for leafNode in leafNodes:
        (contractPath, contractName) = os.path.split(leafNode)
        contractPath = os.path.join(contractPath, contractName)
        contractName = contractName[:len(contractName) - 4]
        targetPath = os.path.join(outputDir, contractName + "_packed.sol")
        version, contract = getPackedContract(contractPath, nodeModulePath)
        if version == "failed":
            continue
        packedLeafNode = version + "\n" + contract
        with open(targetPath, 'w') as f:
            f.write(packedLeafNode)
