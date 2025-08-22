#!/bin/bash
# UFPS Installation Testing Script
# Tests installation, functionality, and uninstallation

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test configuration
TEST_DIR="/tmp/ufps_test_$$"
BACKUP_DIR="/tmp/ufps_backup_$$"
INSTALL_DIR="$HOME/.ufps"
BIN_PATH="$HOME/.local/bin/ufps"

echo "======================================"
echo "UFPS Installation Test Suite"
echo "======================================"
echo ""

# Function to print colored output
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
        return 1
    fi
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Backup existing installation if present
backup_existing() {
    if [ -d "$INSTALL_DIR" ]; then
        print_info "Backing up existing installation..."
        mv "$INSTALL_DIR" "$BACKUP_DIR"
    fi
    if [ -f "$BIN_PATH" ]; then
        mv "$BIN_PATH" "${BIN_PATH}.backup"
    fi
}

# Restore backup
restore_backup() {
    if [ -d "$BACKUP_DIR" ]; then
        print_info "Restoring original installation..."
        rm -rf "$INSTALL_DIR" 2>/dev/null || true
        mv "$BACKUP_DIR" "$INSTALL_DIR"
    fi
    if [ -f "${BIN_PATH}.backup" ]; then
        rm -f "$BIN_PATH" 2>/dev/null || true
        mv "${BIN_PATH}.backup" "$BIN_PATH"
    fi
}

# Cleanup function
cleanup() {
    print_info "Cleaning up..."
    rm -rf "$TEST_DIR" 2>/dev/null || true
    # Only restore if we made a backup
    if [ -d "$BACKUP_DIR" ] || [ -f "${BIN_PATH}.backup" ]; then
        restore_backup
    fi
}

# Set trap for cleanup on exit
trap cleanup EXIT

# Test 1: Check prerequisites
test_prerequisites() {
    echo ""
    echo "Test 1: Prerequisites Check"
    echo "----------------------------"
    
    # Check Python version
    python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
    if python3 -c 'import sys; exit(0 if sys.version_info >= (3,8) else 1)'; then
        print_status 0 "Python version check ($python_version >= 3.8)"
    else
        print_status 1 "Python version check ($python_version < 3.8)"
        return 1
    fi
    
    # Check git
    if command -v git &> /dev/null; then
        print_status 0 "Git is installed"
    else
        print_status 1 "Git is not installed"
        return 1
    fi
    
    # Check for installation script
    if [ -f "install.py" ]; then
        print_status 0 "install.py exists"
    else
        print_status 1 "install.py not found"
        return 1
    fi
    
    return 0
}

# Test 2: Fresh installation
test_fresh_install() {
    echo ""
    echo "Test 2: Fresh Installation"
    echo "--------------------------"
    
    backup_existing
    
    # Run installation
    print_info "Running installer..."
    if python3 install.py > /tmp/ufps_install_log.txt 2>&1; then
        print_status 0 "Installation completed"
    else
        print_status 1 "Installation failed"
        cat /tmp/ufps_install_log.txt
        return 1
    fi
    
    # Check installation directory
    if [ -d "$INSTALL_DIR" ]; then
        print_status 0 "Installation directory created"
    else
        print_status 1 "Installation directory not found"
        return 1
    fi
    
    # Check virtual environment
    if [ -d "$INSTALL_DIR/venv" ]; then
        print_status 0 "Virtual environment created"
    else
        print_status 1 "Virtual environment not found"
        return 1
    fi
    
    # Check executable
    if [ -f "$BIN_PATH" ]; then
        print_status 0 "Executable created"
    else
        print_status 1 "Executable not found"
        return 1
    fi
    
    # Check config file
    if [ -f "$INSTALL_DIR/config.json" ]; then
        print_status 0 "Configuration saved"
    else
        print_status 1 "Configuration not found"
        return 1
    fi
    
    return 0
}

# Test 3: Check installed components
test_components() {
    echo ""
    echo "Test 3: Component Verification"
    echo "-------------------------------"
    
    # Check Python packages
    print_info "Checking Python packages..."
    packages=("torch" "torchvision" "opencv-python" "numpy" "rich" "questionary")
    for pkg in "${packages[@]}"; do
        if "$INSTALL_DIR/venv/bin/python" -c "import $pkg" 2>/dev/null; then
            print_status 0 "Package $pkg installed"
        else
            print_status 1 "Package $pkg not found"
        fi
    done
    
    # Check RIFE
    if [ -d "$INSTALL_DIR/RIFE" ]; then
        print_status 0 "RIFE repository present"
    else
        print_status 1 "RIFE repository not found"
    fi
    
    # Check models
    if [ -d "$INSTALL_DIR/models" ]; then
        model_count=$(ls "$INSTALL_DIR/models"/*.pkl 2>/dev/null | wc -l)
        if [ "$model_count" -ge 3 ]; then
            print_status 0 "AI models downloaded ($model_count files)"
        else
            print_status 1 "AI models incomplete ($model_count files)"
        fi
    else
        print_status 1 "Models directory not found"
    fi
    
    return 0
}

# Test 4: CLI functionality
test_cli() {
    echo ""
    echo "Test 4: CLI Functionality"
    echo "-------------------------"
    
    # Test help/version output
    if "$BIN_PATH" --help 2>/dev/null | grep -q "UFPS"; then
        print_status 0 "CLI executes successfully"
    else
        # The CLI might not have --help, try running it with timeout
        if timeout 2 "$BIN_PATH" < /dev/null 2>/dev/null | grep -q "UFPS\|video"; then
            print_status 0 "CLI executes successfully"
        else
            print_status 1 "CLI execution failed"
        fi
    fi
    
    return 0
}

# Test 5: Reinstallation over existing
test_reinstall() {
    echo ""
    echo "Test 5: Reinstallation Test"
    echo "----------------------------"
    
    print_info "Running installer again..."
    if python3 install.py > /tmp/ufps_reinstall_log.txt 2>&1; then
        print_status 0 "Reinstallation handled correctly"
    else
        print_status 1 "Reinstallation failed"
        return 1
    fi
    
    # Verify everything still works
    if [ -f "$BIN_PATH" ] && [ -d "$INSTALL_DIR" ]; then
        print_status 0 "Installation intact after reinstall"
    else
        print_status 1 "Installation broken after reinstall"
        return 1
    fi
    
    return 0
}

# Test 6: Uninstallation
test_uninstall() {
    echo ""
    echo "Test 6: Uninstallation"
    echo "----------------------"
    
    print_info "Running uninstaller..."
    if echo "y" | python3 uninstall.py > /tmp/ufps_uninstall_log.txt 2>&1; then
        print_status 0 "Uninstallation completed"
    else
        print_status 1 "Uninstallation failed"
        cat /tmp/ufps_uninstall_log.txt
        return 1
    fi
    
    # Check removal
    if [ ! -d "$INSTALL_DIR" ]; then
        print_status 0 "Installation directory removed"
    else
        print_status 1 "Installation directory still exists"
        return 1
    fi
    
    if [ ! -f "$BIN_PATH" ]; then
        print_status 0 "Executable removed"
    else
        print_status 1 "Executable still exists"
        return 1
    fi
    
    return 0
}

# Main test execution
main() {
    local failed=0
    
    # Run tests
    test_prerequisites || failed=1
    
    if [ $failed -eq 0 ]; then
        test_fresh_install || failed=1
    fi
    
    if [ $failed -eq 0 ]; then
        test_components || failed=1
    fi
    
    if [ $failed -eq 0 ]; then
        test_cli || failed=1
    fi
    
    if [ $failed -eq 0 ]; then
        test_reinstall || failed=1
    fi
    
    if [ $failed -eq 0 ]; then
        test_uninstall || failed=1
    fi
    
    # Summary
    echo ""
    echo "======================================"
    if [ $failed -eq 0 ]; then
        echo -e "${GREEN}All tests passed!${NC}"
    else
        echo -e "${RED}Some tests failed!${NC}"
    fi
    echo "======================================"
    
    return $failed
}

# Run main
main
exit $?