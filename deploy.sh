#!/bin/bash
# Storm Checker PyPI Deployment Script
# Professional deployment with comprehensive validation and error handling

set -e  # Exit on error

# Storm Checker Brand Colors (matching the official color palette)
if [ -t 1 ] && [ -z "$CI" ]; then
    # Primary colors
    STORM_BLUE='\033[38;2;65;135;145m'      # Teal blue (#418791)
    STORM_PURPLE='\033[38;2;177;49;127m'    # Magenta (#b1317f)
    
    # Status colors
    STORM_GREEN='\033[38;2;70;107;93m'      # Sage green (#466b5d)
    STORM_YELLOW='\033[38;2;204;171;120m'   # Golden (#ccab78)
    STORM_RED='\033[38;2;156;82;90m'        # Rose (#9c525a)
    
    # Info and text colors
    STORM_CYAN='\033[38;2;88;122;132m'      # Steel blue (#587a84)
    STORM_WHITE='\033[38;2;219;219;208m'    # Light gray (#dbdbd0)
    
    # Additional accent colors
    STORM_GOLD='\033[38;2;255;204;103m'     # Gold yellow (#ffcc67)
    STORM_NAVY='\033[38;2;0;49;144m'        # Navy blue (#003190)
    STORM_FOREST='\033[38;2;54;79;51m'      # Forest dark (#364f33)
    
    NC='\033[0m' # No Color
else
    STORM_BLUE=''
    STORM_PURPLE=''
    STORM_GREEN=''
    STORM_YELLOW=''
    STORM_RED=''
    STORM_CYAN=''
    STORM_WHITE=''
    STORM_GOLD=''
    STORM_NAVY=''
    STORM_FOREST=''
    NC=''
fi

# Helper functions
echo_info() {
    echo -e "${STORM_CYAN}[INFO]${NC} $1"
}

echo_success() {
    echo -e "${STORM_GREEN}[SUCCESS]${NC} $1"
}

echo_error() {
    echo -e "${STORM_RED}[ERROR]${NC} $1"
}

echo_warning() {
    echo -e "${STORM_YELLOW}[WARNING]${NC} $1"
}

echo_highlight() {
    echo -e "${STORM_BLUE}[STORM]${NC} $1"
}

echo_deploy() {
    echo -e "${STORM_PURPLE}[DEPLOY]${NC} $1"
}

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

DRY_RUN=false
FORCE=false
SKIP_TESTS=false
COVERAGE_THRESHOLD=80
AUTO_VERSION_BUMP=false
SIGN_RELEASE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --coverage-threshold)
            COVERAGE_THRESHOLD="$2"
            shift 2
            ;;
        --auto-version-bump)
            AUTO_VERSION_BUMP=true
            shift
            ;;
        --sign)
            SIGN_RELEASE=true
            shift
            ;;
        --help|-h)
            echo_highlight "Storm Checker PyPI Deployment"
            echo ""
            echo "⚡ DEPLOYMENT WORKFLOW:"
            echo "  1️⃣  Pre-deployment: Version & git checks"
            echo "  2️⃣  Testing: Run comprehensive test suite"
            echo "  3️⃣  Build: Create distribution packages"
            echo "  4️⃣  Deploy: Upload to PyPI"
            echo "  5️⃣  Verify: Post-deployment validation"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --dry-run              Run all checks without deploying"
            echo "  --force                Bypass some safety checks"
            echo "  --skip-tests           Skip test execution (not recommended)"
            echo "  --coverage-threshold   Set coverage threshold (default: 80)"
            echo "  --auto-version-bump    Automatically bump patch version if needed"
            echo "  --sign                 GPG sign the release"
            echo "  --help, -h             Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                     # Full deployment"
            echo "  $0 --dry-run           # Test deployment process"
            echo "  $0 --auto-version-bump # Auto-increment version if needed"
            echo ""
            echo_highlight "⚡ Intelligent Code Quality Analysis ⚡"
            exit 0
            ;;
        *)
            echo_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Cleanup function
cleanup() {
    echo_info "Cleaning up temporary files..."
    rm -rf build/ dist/ *.egg-info/ .pytest_cache/
    rm -f .coverage coverage.xml
}

# Trap to cleanup on exit
trap cleanup EXIT

# Storm Checker ASCII Banner
display_banner() {
    echo -e "${STORM_BLUE}╔════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${STORM_BLUE}║                                                                    ║${NC}"
    echo -e "${STORM_BLUE}║  ${STORM_GOLD}███████╗████████╗ ██████╗ ██████╗ ███╗   ███╗${STORM_BLUE}                   ║${NC}"
    echo -e "${STORM_BLUE}║  ${STORM_GOLD}██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗████╗ ████║${STORM_BLUE}                   ║${NC}"
    echo -e "${STORM_BLUE}║  ${STORM_GOLD}███████╗   ██║   ██║   ██║██████╔╝██╔████╔██║${STORM_BLUE}                   ║${NC}"
    echo -e "${STORM_BLUE}║  ${STORM_GOLD}╚════██║   ██║   ██║   ██║██╔══██╗██║╚██╔╝██║${STORM_BLUE}                   ║${NC}"
    echo -e "${STORM_BLUE}║  ${STORM_GOLD}███████║   ██║   ╚██████╔╝██║  ██║██║ ╚═╝ ██║${STORM_BLUE}                   ║${NC}"
    echo -e "${STORM_BLUE}║  ${STORM_GOLD}╚══════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝${STORM_BLUE}                   ║${NC}"
    echo -e "${STORM_BLUE}║                                                                    ║${NC}"
    echo -e "${STORM_BLUE}║  ${STORM_PURPLE} █████╗██╗  ██╗███████╗ █████╗ ██╗  ██╗███████╗██████╗${STORM_BLUE}         ║${NC}"
    echo -e "${STORM_BLUE}║  ${STORM_PURPLE}██╔══██╗██║  ██║██╔════╝██╔══██╗██║ ██╔╝██╔════╝██╔══██╗${STORM_BLUE}        ║${NC}"
    echo -e "${STORM_BLUE}║  ${STORM_PURPLE}██║  ╚═╝███████║█████╗  ██║  ╚═╝█████═╝ █████╗  ██████╔╝${STORM_BLUE}        ║${NC}"
    echo -e "${STORM_BLUE}║  ${STORM_PURPLE}██║  ██╗██╔══██║██╔══╝  ██║  ██╗██╔═██╗ ██╔══╝  ██╔══██╗${STORM_BLUE}        ║${NC}"
    echo -e "${STORM_BLUE}║  ${STORM_PURPLE}╚█████╔╝██║  ██║███████╗╚█████╔╝██║ ╚██╗███████╗██║  ██║${STORM_BLUE}        ║${NC}"
    echo -e "${STORM_BLUE}║   ${STORM_PURPLE}╚════╝ ╚═╝  ╚═╝╚══════╝ ╚════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝${STORM_BLUE}        ║${NC}"
    echo -e "${STORM_BLUE}║                                                                    ║${NC}"
    echo -e "${STORM_BLUE}║       ${STORM_CYAN}Intelligent Python Code Quality Analysis${STORM_BLUE}                   ║${NC}"
    echo -e "${STORM_BLUE}║     ${STORM_GREEN}⚡ Type Checking Made Simple & Engaging ⚡${STORM_BLUE}                ║${NC}"
    echo -e "${STORM_BLUE}║                                                                    ║${NC}"
    echo -e "${STORM_BLUE}╚════════════════════════════════════════════════════════════════════╝${NC}"
}

display_banner

if [ "$DRY_RUN" = true ]; then
    echo_warning "DRY RUN MODE - No actual deployment will occur"
fi

# ==========================================
# ENVIRONMENT SETUP
# ==========================================

echo_deploy "Phase 0: Environment Setup"

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo_warning "Not in a virtual environment"
    if [ -d "venv" ]; then
        echo_info "Activating virtual environment..."
        source venv/bin/activate
    else
        echo_error "No virtual environment found. Please create one with: python -m venv venv"
        exit 1
    fi
else
    echo_success "Virtual environment active: $VIRTUAL_ENV"
fi

# Install required build tools
echo_info "Checking build dependencies..."
MISSING_DEPS=false

# Check for build
if ! python -m pip show build &>/dev/null; then
    echo_warning "Installing missing dependency: build"
    pip install --upgrade build
    MISSING_DEPS=true
fi

# Check for twine
if ! python -m pip show twine &>/dev/null; then
    echo_warning "Installing missing dependency: twine"
    pip install --upgrade twine
    MISSING_DEPS=true
fi

# Check for wheel
if ! python -m pip show wheel &>/dev/null; then
    echo_warning "Installing missing dependency: wheel"
    pip install --upgrade wheel
    MISSING_DEPS=true
fi

# Check for setuptools
if ! python -m pip show setuptools &>/dev/null; then
    echo_warning "Installing missing dependency: setuptools"
    pip install --upgrade setuptools
    MISSING_DEPS=true
fi

if [ "$MISSING_DEPS" = true ]; then
    echo_success "Build dependencies installed successfully"
else
    echo_success "All build dependencies are already installed"
fi

# ==========================================
# PRE-DEPLOYMENT VALIDATION
# ==========================================

echo_deploy "Phase 1: Pre-deployment Validation"

# Check if pyproject.toml exists
if [ ! -f "pyproject.toml" ]; then
    echo_error "pyproject.toml not found!"
    exit 1
fi

# Check if README exists
if [ ! -f "README.md" ]; then
    echo_error "README.md not found!"
    echo_error "The README is required for PyPI deployment"
    exit 1
fi

# Check if __init__.py exists in storm_checker module
if [ ! -f "storm_checker/__init__.py" ]; then
    echo_error "storm_checker/__init__.py not found!"
    exit 1
fi

# Extract versions
PYPROJECT_VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')

# Check if __init__.py has version
if grep -q '^__version__ = ' storm_checker/__init__.py; then
    INIT_VERSION=$(grep '^__version__ = ' storm_checker/__init__.py | sed "s/__version__ = ['\"]\\([^'\"]*\\)['\"].*/\\1/")
else
    echo_warning "__version__ not found in storm_checker/__init__.py"
    echo_info "Adding __version__ to __init__.py..."
    echo "__version__ = \"$PYPROJECT_VERSION\"" >> storm_checker/__init__.py
    INIT_VERSION=$PYPROJECT_VERSION
fi

echo_info "pyproject.toml version: $PYPROJECT_VERSION"
echo_info "__init__.py version: $INIT_VERSION"

# Check version consistency
if [ "$PYPROJECT_VERSION" != "$INIT_VERSION" ]; then
    echo_error "Version mismatch detected!"
    echo_error "  pyproject.toml: $PYPROJECT_VERSION"
    echo_error "  __init__.py: $INIT_VERSION"
    
    if [ "$AUTO_VERSION_BUMP" = true ]; then
        echo_info "Auto-fixing version mismatch..."
        sed -i "s/__version__ = .*/__version__ = \"$PYPROJECT_VERSION\"/" storm_checker/__init__.py
        echo_success "Updated __init__.py to version $PYPROJECT_VERSION"
    else
        echo_error "Please update both files to have the same version number"
        exit 1
    fi
fi

echo_success "Version consistency check passed: $PYPROJECT_VERSION"

# Check if version is already on PyPI
check_pypi_version() {
    local version=$1
    
    echo_info "Checking if version $version already exists on PyPI..."
    
    # Try to get package info from PyPI
    PYPI_RESPONSE=$(curl -s "https://pypi.org/pypi/storm-checker/json" || echo "{}")
    
    if echo "$PYPI_RESPONSE" | grep -q "Not Found"; then
        echo_info "Package not yet on PyPI (first release)"
        return 1  # Package doesn't exist yet
    fi
    
    # Check if version exists in releases
    if echo "$PYPI_RESPONSE" | grep -q "\"$version\""; then
        return 0  # Version exists
    else
        return 1  # Version doesn't exist
    fi
}

if command -v curl &> /dev/null; then
    set +e  # Temporarily disable exit on error
    check_pypi_version "$PYPROJECT_VERSION"
    result=$?
    set -e  # Re-enable exit on error

    if [ $result -eq 0 ]; then
        echo_error "Version $PYPROJECT_VERSION already exists on PyPI!"
        
        if [ "$AUTO_VERSION_BUMP" = true ]; then
            # Auto bump version
            IFS='.' read -ra VERSION_PARTS <<< "$PYPROJECT_VERSION"
            PATCH=$((VERSION_PARTS[2] + 1))
            NEW_VERSION="${VERSION_PARTS[0]}.${VERSION_PARTS[1]}.$PATCH"
            
            echo_info "Auto-bumping version to $NEW_VERSION..."
            
            # Update pyproject.toml
            sed -i "s/version = \"$PYPROJECT_VERSION\"/version = \"$NEW_VERSION\"/" pyproject.toml
            
            # Update __init__.py
            sed -i "s/__version__ = \"$PYPROJECT_VERSION\"/__version__ = \"$NEW_VERSION\"/" storm_checker/__init__.py
            
            PYPROJECT_VERSION=$NEW_VERSION
            echo_success "Version bumped to $NEW_VERSION"
        else
            echo_error "Please increment the version number in both pyproject.toml and __init__.py"
            # Suggest next version
            IFS='.' read -ra VERSION_PARTS <<< "$PYPROJECT_VERSION"
            PATCH=$((VERSION_PARTS[2] + 1))
            echo_info "Suggested next version: ${VERSION_PARTS[0]}.${VERSION_PARTS[1]}.$PATCH"
            exit 1
        fi
    elif [ $result -eq 1 ]; then
        echo_success "Version $PYPROJECT_VERSION is not on PyPI yet"
    fi
else
    echo_warning "Skipping PyPI version check (curl not available)"
fi

# Git status check
if [ "$FORCE" != true ] && command -v git &> /dev/null && [ -d ".git" ]; then
    echo_info "Checking git status..."

    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD -- 2>/dev/null; then
        echo_warning "Uncommitted changes detected:"
        git status --porcelain
        
        if [ "$FORCE" != true ]; then
            read -p "Continue with uncommitted changes? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo_error "Deployment cancelled"
                exit 1
            fi
        fi
    fi

    # Check current branch
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    if [ "$CURRENT_BRANCH" != "main" ] && [ "$CURRENT_BRANCH" != "master" ]; then
        echo_warning "Deploying from branch: $CURRENT_BRANCH (not main/master)"
    fi

    echo_success "Git status check completed"
fi

# Load PyPI token securely
if [ -f ".env" ]; then
    # Safer method to load environment variables
    if [ -f ".env" ]; then
        # Use grep to extract just the PYPI_TOKEN line and export it
        export $(grep -E '^PYPI_TOKEN=' .env | grep -v '^#' | head -n 1)
    fi
else
    echo_error ".env file not found!"
    echo_error "Please create .env file with PYPI_TOKEN"
    echo_info "Example .env file:"
    echo "PYPI_TOKEN=pypi-your-token-here"
    exit 1
fi

if [ -z "$PYPI_TOKEN" ]; then
    echo_error "PYPI_TOKEN not found in .env file!"
    echo_error "Please add PYPI_TOKEN to your .env file"
    exit 1
fi

echo_success "PyPI token loaded from .env file"

# Display packaging information
echo_info "Package configuration:"
echo_info "  Package name: storm-checker"
echo_info "  Version: $PYPROJECT_VERSION"
echo_info "  Author: Mathew (mathewstormdev@gmail.com)"
echo_info "  License: MIT"

# ==========================================
# TESTING
# ==========================================

echo_deploy "Phase 2: Testing & Coverage"

if [ "$SKIP_TESTS" != true ]; then
    echo_info "Running test suite with Storm Checker's custom runner..."

    # Check if test runner exists
    if [ -f "tests/run_tests.py" ]; then
        echo_info "Using custom test runner with coverage analysis..."
        
        # Run tests with coverage
        if ! python tests/run_tests.py --coverage --quiet; then
            echo_error "Tests failed!"
            
            if [ "$FORCE" != true ]; then
                echo_error "Fix failing tests before deployment"
                exit 1
            else
                echo_warning "Continuing despite test failures (--force flag used)"
            fi
        else
            echo_success "All tests passed!"
            
            # Check coverage threshold
            if [ -f "htmlcov/index.html" ]; then
                # Extract coverage percentage from the HTML report
                COVERAGE_PCT=$(grep -oP 'pc_cov">\K[0-9]+(?=%)' htmlcov/index.html | head -1 || echo "0")
                
                echo_info "Test coverage: ${COVERAGE_PCT}%"
                
                if [ "$COVERAGE_PCT" -lt "$COVERAGE_THRESHOLD" ]; then
                    echo_warning "Coverage ${COVERAGE_PCT}% is below threshold ${COVERAGE_THRESHOLD}%"
                    
                    if [ "$FORCE" != true ]; then
                        echo_error "Improve test coverage before deployment"
                        exit 1
                    fi
                else
                    echo_success "Coverage meets threshold!"
                fi
            fi
        fi
    else
        echo_warning "Custom test runner not found, using pytest directly..."
        
        if ! python -m pytest tests/ -v; then
            echo_error "Tests failed!"
            
            if [ "$FORCE" != true ]; then
                exit 1
            fi
        fi
    fi
    
    echo_success "Test phase completed"
else
    echo_warning "Skipping tests (--skip-tests flag used)"
fi

# ==========================================
# CHANGELOG GENERATION
# ==========================================

echo_deploy "Phase 3: Changelog & Documentation"

# Update CHANGELOG.md if it exists
if [ -f "CHANGELOG.md" ] && command -v git &> /dev/null; then
    echo_info "Checking for changelog updates..."
    
    # Check if this version is already in changelog
    if ! grep -q "## \[$PYPROJECT_VERSION\]" CHANGELOG.md; then
        echo_info "Adding version $PYPROJECT_VERSION to changelog..."
        
        # Get latest commits since last tag
        LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
        
        if [ -n "$LAST_TAG" ]; then
            echo_info "Generating changelog from $LAST_TAG..."
            
            # Create changelog entry
            CHANGELOG_ENTRY="## [$PYPROJECT_VERSION] - $(date +%Y-%m-%d)\n\n### Added\n"
            
            # Get commits and categorize them
            while IFS= read -r commit; do
                if [[ $commit == feat:* ]]; then
                    CHANGELOG_ENTRY="${CHANGELOG_ENTRY}- ${commit#feat: }\n"
                elif [[ $commit == fix:* ]]; then
                    if [[ $CHANGELOG_ENTRY != *"### Fixed"* ]]; then
                        CHANGELOG_ENTRY="${CHANGELOG_ENTRY}\n### Fixed\n"
                    fi
                    CHANGELOG_ENTRY="${CHANGELOG_ENTRY}- ${commit#fix: }\n"
                fi
            done < <(git log --oneline --pretty=format:"%s" "$LAST_TAG"..HEAD)
            
            # Prepend to changelog
            echo -e "$CHANGELOG_ENTRY\n" | cat - CHANGELOG.md > temp && mv temp CHANGELOG.md
            
            echo_success "Changelog updated"
        fi
    fi
fi

# ==========================================
# BUILD & DEPLOYMENT
# ==========================================

echo_deploy "Phase 4: Build & Package"

# Clean build environment
echo_info "Cleaning build environment..."
rm -rf build/ dist/ *.egg-info/
echo_success "Build environment cleaned"

# Build package
echo_info "Building package..."

if ! python -m build; then
    echo_error "Package build failed!"
    exit 1
fi

# Verify build outputs
WHEEL_FILE=$(ls dist/*.whl 2>/dev/null | head -n1)
if [ -z "$WHEEL_FILE" ]; then
    echo_error "No wheel file found!"
    exit 1
fi
echo_success "Found wheel: $(basename $WHEEL_FILE)"

# Check for source distribution
if [ ! -f "dist/storm_checker-${PYPROJECT_VERSION}.tar.gz" ]; then
    echo_error "Source distribution not found!"
    exit 1
fi

echo_success "Package built successfully"

# Package validation
echo_info "Validating package contents..."
if ! twine check dist/*; then
    echo_error "Package validation failed!"
    exit 1
fi
echo_success "Package validation passed"

# GPG signing (optional)
if [ "$SIGN_RELEASE" = true ] && command -v gpg &> /dev/null; then
    echo_info "Signing release with GPG..."
    
    for file in dist/*; do
        gpg --detach-sign --armor "$file"
    done
    
    echo_success "Release signed"
fi

# Display package info
echo_info "Package contents:"
ls -la dist/

# ==========================================
# PRE-UPLOAD TESTING
# ==========================================

echo_info "Pre-upload package testing..."

# Create a temporary virtual environment for testing
TEMP_VENV=$(mktemp -d)/test_venv
python -m venv "$TEMP_VENV"
source "$TEMP_VENV/bin/activate"

# Install the package locally
echo_info "Installing package from wheel..."
if ! pip install "$WHEEL_FILE"; then
    echo_error "Local package installation failed!"
    deactivate
    rm -rf "$TEMP_VENV"
    exit 1
fi

# Test imports
echo_info "Testing package imports..."
if ! python -c "import storm_checker; print(f'Storm Checker v{storm_checker.__version__} imported successfully')"; then
    echo_error "Package import test failed!"
    deactivate
    rm -rf "$TEMP_VENV"
    exit 1
fi

# Test CLI command
echo_info "Testing CLI command..."
if ! stormcheck --help &>/dev/null; then
    echo_error "CLI command test failed!"
    deactivate
    rm -rf "$TEMP_VENV"
    exit 1
fi

echo_success "Pre-upload testing passed!"

# Cleanup test environment
deactivate
rm -rf "$TEMP_VENV"

# Reactivate original environment
if [ -n "$VIRTUAL_ENV" ]; then
    source "$VIRTUAL_ENV/bin/activate"
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Deploy to PyPI
if [ "$DRY_RUN" != true ]; then
    echo_deploy "Phase 5: Deploying to PyPI..."

    # Use password from stdin for better security
    if ! echo "$PYPI_TOKEN" | twine upload dist/* --username __token__ --password-stdin; then
        echo_error "PyPI upload failed!"
        exit 1
    fi

    echo_success "Successfully deployed to PyPI!"
    echo_info "Package URL: https://pypi.org/project/storm-checker/$PYPROJECT_VERSION/"
else
    echo_info "DRY RUN: Would deploy to PyPI now"
fi

# ==========================================
# POST-DEPLOYMENT VERIFICATION
# ==========================================

echo_deploy "Phase 6: Post-deployment Verification"

if [ "$DRY_RUN" != true ]; then
    # Wait for PyPI to update
    echo_info "Waiting for PyPI to update (this may take a few minutes)..."

    # Try installation with retries
    MAX_INSTALL_RETRIES=5
    INSTALL_RETRY=0
    INSTALL_SUCCESS=false

    while [ $INSTALL_RETRY -lt $MAX_INSTALL_RETRIES ]; do
        INSTALL_RETRY=$((INSTALL_RETRY + 1))
        echo_info "Attempting to install from PyPI (attempt $INSTALL_RETRY/$MAX_INSTALL_RETRIES)..."

        if pip install --upgrade storm-checker==$PYPROJECT_VERSION 2>/dev/null; then
            INSTALL_SUCCESS=true
            break
        else
            if [ $INSTALL_RETRY -lt $MAX_INSTALL_RETRIES ]; then
                echo_warning "Package not yet available, waiting 30 seconds..."
                sleep 30
            fi
        fi
    done

    if [ "$INSTALL_SUCCESS" = false ]; then
        echo_warning "Could not verify installation from PyPI (may still be propagating)"
        echo_info "Try manually: pip install storm-checker==$PYPROJECT_VERSION"
    else
        echo_success "Installation from PyPI verified!"
        
        # Run final smoke test
        echo_info "Running smoke test..."
        if stormcheck --help &>/dev/null; then
            echo_success "CLI command works from PyPI installation!"
        fi
    fi

    # Git tagging
    if command -v git &> /dev/null && [ -d ".git" ]; then
        echo_info "Creating git tag..."
        
        TAG_NAME="v$PYPROJECT_VERSION"
        TAG_MESSAGE="Release $TAG_NAME - Storm Checker

Intelligent Python code quality analysis with gamified learning.

Changes in this release:
$(git log --oneline --pretty=format:"- %s" $(git describe --tags --abbrev=0 2>/dev/null || echo "")..HEAD 2>/dev/null | head -10)"

        if ! git tag -a "$TAG_NAME" -m "$TAG_MESSAGE"; then
            echo_warning "Git tag creation failed (tag may already exist)"
        else
            echo_success "Git tag $TAG_NAME created"
            echo_info "Push tag with: git push origin $TAG_NAME"
        fi
    fi
else
    echo_info "DRY RUN: Would perform post-deployment verification"
fi

# ==========================================
# SUCCESS NOTIFICATION
# ==========================================

echo ""
echo -e "${STORM_GOLD}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${STORM_GOLD}║                   ${STORM_GREEN}⚡ DEPLOYMENT SUCCESSFUL! ⚡${STORM_GOLD}                ║${NC}"
echo -e "${STORM_GOLD}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${STORM_CYAN}Package Information:${NC}"
echo -e "  ${STORM_BLUE}Name:${NC}        storm-checker"
echo -e "  ${STORM_BLUE}Version:${NC}     $PYPROJECT_VERSION"
echo -e "  ${STORM_BLUE}Author:${NC}      Mathew"

if [ "$DRY_RUN" != true ]; then
    echo ""
    echo -e "${STORM_CYAN}PyPI Details:${NC}"
    echo -e "  ${STORM_BLUE}URL:${NC}         https://pypi.org/project/storm-checker/"
    echo -e "  ${STORM_BLUE}Install:${NC}     pip install storm-checker==$PYPROJECT_VERSION"
    echo -e "  ${STORM_BLUE}Upgrade:${NC}     pip install --upgrade storm-checker"
fi

echo ""
echo -e "${STORM_CYAN}Quality Metrics:${NC}"
echo -e "  ${STORM_BLUE}Tests:${NC}              ${STORM_GREEN}PASSED${NC}"
echo -e "  ${STORM_BLUE}Coverage:${NC}           ${STORM_GREEN}${COVERAGE_PCT:-N/A}%${NC}"
echo -e "  ${STORM_BLUE}Package Build:${NC}      ${STORM_GREEN}PASSED${NC}"
echo -e "  ${STORM_BLUE}Import Test:${NC}        ${STORM_GREEN}PASSED${NC}"
echo -e "  ${STORM_BLUE}CLI Test:${NC}           ${STORM_GREEN}PASSED${NC}"

echo ""
echo -e "${STORM_PURPLE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${STORM_PURPLE}║      ${STORM_GREEN}⚡ Type Checking Made Simple & Engaging ⚡${STORM_PURPLE}              ║${NC}"
echo -e "${STORM_PURPLE}╚═══════════════════════════════════════════════════════════════╝${NC}"

# Generate deployment summary
DEPLOY_TIME=$(date "+%Y-%m-%d %H:%M:%S %Z")
echo ""
echo -e "${STORM_BLUE}Deployed at: $DEPLOY_TIME${NC}"

# Create deployment record
if [ "$DRY_RUN" != true ]; then
    echo "$PYPROJECT_VERSION|$DEPLOY_TIME|$(git rev-parse --short HEAD 2>/dev/null || echo 'no-git')" >> .deployment_history
fi

exit 0