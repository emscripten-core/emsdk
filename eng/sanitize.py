#!/usr/bin/env python3
import json
import os
import shutil
import sys


def glob(path):
    return [os.path.join(path, filename) for filename in os.listdir(path)]


def remove(*paths):
    for path in paths:
        path = os.path.abspath(path)
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        except OSError as error:
            print(error)


def rewrite_package_json(path):
    package = open(path, "r+")
    settings = json.load(package)
    settings["devDependencies"] = {}
    package.seek(0)
    package.truncate()
    json.dump(settings, package, indent=4)
    package.close()


emscripten_path = sys.argv[1]
node_root = sys.argv[2]
node_paths = glob(node_root)
upgrade = False

# Add the local node bin directory to the path so that
# npm can find it when doing the updating or pruning
os.environ["PATH"] = os.path.join(node_paths[0], "bin") + os.pathsep + os.environ["PATH"]

def update_npm(path):
    try:
        os.chdir(os.path.join(path, "lib"))
        os.system("npm install npm@latest")
        os.system("npm install npm@latest")
        prune()
    except OSError as error:
        print("npm update failed")
        print(error)


def remove_npm(path):
    os.chdir(path)
    remove("bin/npx", "bin/npm", "include", "lib", "share")


def prune():
    try:
        os.system("npm prune --production")
    except OSError as error:
        print("npm prune failed")
        print(error)

if upgrade:
    for path in node_paths:
        update_npm(path)

os.chdir(emscripten_path)
rewrite_package_json("package.json")
try:
    os.system("npm audit fix")
except OSError as error:
    print("npm audit fix failed")
    print(error)

prune()

if not upgrade:
    for path in node_paths:
        remove_npm(path)
