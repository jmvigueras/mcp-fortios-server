#!/bin/bash

# Release script for MCP FortiOS Server
# Usage: ./scripts/release.sh [patch|minor|major] or ./scripts/release.sh v1.0.1

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get current version from pyproject.toml
CURRENT_VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')

echo -e "${GREEN}Current version: ${CURRENT_VERSION}${NC}"

# Check if working directory is clean
if ! git diff-index --quiet HEAD --; then
    echo -e "${RED}Error: Working directory is not clean. Please commit or stash changes first.${NC}"
    exit 1
fi

# Function to increment version
increment_version() {
    local version=$1
    local increment_type=$2
    
    IFS='.' read -ra VERSION_PARTS <<< "$version"
    major=${VERSION_PARTS[0]}
    minor=${VERSION_PARTS[1]}
    patch=${VERSION_PARTS[2]}
    
    case $increment_type in
        "patch")
            patch=$((patch + 1))
            ;;
        "minor")
            minor=$((minor + 1))
            patch=0
            ;;
        "major")
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        *)
            echo -e "${RED}Invalid increment type. Use: patch, minor, or major${NC}"
            exit 1
            ;;
    esac
    
    echo "${major}.${minor}.${patch}"
}

# Determine new version
if [[ $1 =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    # Direct version specified (e.g., v1.0.1)
    NEW_VERSION=${1#v}  # Remove 'v' prefix
    TAG_VERSION=$1
elif [[ $1 =~ ^(patch|minor|major)$ ]]; then
    # Increment type specified
    NEW_VERSION=$(increment_version $CURRENT_VERSION $1)
    TAG_VERSION="v${NEW_VERSION}"
else
    echo -e "${RED}Usage: $0 [patch|minor|major] or $0 v1.0.1${NC}"
    exit 1
fi

echo -e "${YELLOW}New version will be: ${NEW_VERSION}${NC}"
echo -e "${YELLOW}Git tag will be: ${TAG_VERSION}${NC}"

# Confirm with user
read -p "Continue with release? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Release cancelled${NC}"
    exit 1
fi

# Update pyproject.toml
echo -e "${GREEN}Updating pyproject.toml...${NC}"
sed -i '' "s/^version = \".*\"/version = \"${NEW_VERSION}\"/" pyproject.toml

# Update app/__init__.py
echo -e "${GREEN}Updating app/__init__.py...${NC}"
sed -i '' "s/^__version__ = \".*\"/__version__ = \"${NEW_VERSION}\"/" app/__init__.py

# Regenerate lock file
echo -e "${GREEN}Regenerating uv.lock file...${NC}"
uv lock --upgrade

# Run simple tests
echo -e "${GREEN}Running tests...${NC}"
if command -v uv >/dev/null 2>&1; then
    uv run pytest tests/test_basic.py -v
else
    echo -e "${YELLOW}Warning: uv not found, skipping tests${NC}"
fi

# Commit version changes
echo -e "${GREEN}Committing version changes...${NC}"
git add pyproject.toml app/__init__.py uv.lock
git commit -m "chore: bump version to ${NEW_VERSION}"

# Create and push tag
echo -e "${GREEN}Creating and pushing tag ${TAG_VERSION}...${NC}"
git tag -a "${TAG_VERSION}" -m "Release ${TAG_VERSION}"
git push origin main
git push origin "${TAG_VERSION}"

echo -e "${GREEN}✅ Release ${TAG_VERSION} created successfully!${NC}"
echo -e "${GREEN}🚀 GitHub Actions will now build and publish the Docker image.${NC}"
echo -e "${GREEN}📦 Check DockerHub for: jmvigueras/mcp-fortios-server:${TAG_VERSION}${NC}"
echo
echo -e "${GREEN}Release Summary:${NC}"
echo -e "  • Version: ${CURRENT_VERSION} → ${NEW_VERSION}"
echo -e "  • Git tag: ${TAG_VERSION}"
echo -e "  • Files updated: pyproject.toml, app/__init__.py, uv.lock"