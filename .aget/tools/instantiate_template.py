#!/usr/bin/env python3
"""Template Instantiation Tool

Helper tool to instantiate this template for a new agent.

Usage:
    python3 .aget/tools/instantiate_template.py <agent_name> <target_dir>
    python3 .aget/tools/instantiate_template.py --check <target_dir>

Examples:
    # Instantiate template
    python3 .aget/tools/instantiate_template.py invoice-processor ~/github/invoice-processor-AGET

    # Check instantiation
    python3 .aget/tools/instantiate_template.py --check ~/github/invoice-processor-AGET
"""

import sys
import argparse
import json
import shutil
from pathlib import Path
from datetime import datetime


def instantiate_template(agent_name: str, target_dir: str, template_dir: str = None) -> bool:
    """Instantiate template for new agent

    Args:
        agent_name: Name of new agent (e.g., 'invoice-processor')
        target_dir: Target directory for new agent
        template_dir: Template directory (default: current directory)

    Returns:
        True if successful
    """
    if template_dir is None:
        template_dir = Path.cwd()
    else:
        template_dir = Path(template_dir)

    target_path = Path(target_dir).expanduser()

    print("Template Instantiation")
    print("=" * 60)
    print(f"\nAgent Name: {agent_name}")
    print(f"Target Directory: {target_path}")
    print(f"Template Directory: {template_dir}")

    # Validate inputs
    if not template_dir.exists():
        raise FileNotFoundError(f"Template directory not found: {template_dir}")

    if target_path.exists():
        raise FileExistsError(f"Target directory already exists: {target_path}")

    version_file = template_dir / '.aget' / 'version.json'
    if not version_file.exists():
        raise FileNotFoundError(f"Not a valid template (missing .aget/version.json)")

    # Read template version
    with open(version_file) as f:
        template_version = json.load(f)

    print(f"\nTemplate Version: {template_version['aget_version']}")
    print(f"Template Type: {template_version['instance_type']}")

    # Copy template
    print(f"\n[1/4] Copying template files...")
    shutil.copytree(template_dir, target_path, ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc'))
    print(f"  ✅ Copied to {target_path}")

    # Update version.json
    print(f"\n[2/4] Updating agent identity...")
    new_version_file = target_path / '.aget' / 'version.json'

    with open(new_version_file) as f:
        version_data = json.load(f)

    version_data['agent_name'] = agent_name
    version_data['created_at'] = datetime.now().isoformat()
    version_data['instantiated_from'] = template_version['agent_name']

    with open(new_version_file, 'w') as f:
        json.dump(version_data, f, indent=2)

    print(f"  ✅ Updated .aget/version.json")
    print(f"     agent_name: {agent_name}")

    # Update README placeholder
    print(f"\n[3/4] Updating documentation...")
    readme_file = target_path / 'README.md'
    if readme_file.exists():
        with open(readme_file) as f:
            readme_content = f.read()

        readme_content = readme_content.replace(
            'template-document-processor-AGET',
            f'{agent_name}-AGET'
        )

        with open(readme_file, 'w') as f:
            f.write(readme_content)

        print(f"  ✅ Updated README.md")

    # Create initialization checklist
    print(f"\n[4/4] Creating initialization checklist...")
    checklist_file = target_path / 'INITIALIZATION_CHECKLIST.md'

    checklist_content = f"""# Initialization Checklist for {agent_name}-AGET

Created: {datetime.now().strftime('%Y-%m-%d')}
Template Version: {template_version['aget_version']}

## Required Steps

### 1. Update Configuration
- [ ] Update AGENTS.md with agent-specific context
- [ ] Set domain in .aget/version.json
- [ ] Configure models.yaml for your LLM provider

### 2. Customize Processing
- [ ] Define your document schemas in configs/schemas/
- [ ] Update wikitext patterns in configs/wikitext/
- [ ] Configure security rules in configs/security.yaml

### 3. Test Setup
- [ ] Run health check: `python3 scripts/health_check.py --verbose`
- [ ] Test validation: `python3 scripts/validate.py <test_document>`
- [ ] Verify cache: `python3 scripts/cache_setup.py --verify`

### 4. Git Repository
- [ ] Initialize git: `git init`
- [ ] Create repository on GitHub
- [ ] Add remote: `git remote add origin <url>`
- [ ] Initial commit: `git add . && git commit -m "feat: Initialize {agent_name}-AGET"`
- [ ] Push: `git push -u origin main`

### 5. Contract Tests
- [ ] Run contract tests: `python3 -m pytest tests/ -v`
- [ ] All 7 tests should pass

## Optional Enhancements
- [ ] Add custom protocols to .aget/docs/protocols/
- [ ] Create specifications for complex workflows
- [ ] Add domain-specific scripts to scripts/
- [ ] Configure portfolio assignment (if using multi-portfolio setup)

## Verification
```bash
# Sanity check
python3 scripts/health_check.py --verbose

# Contract tests
python3 -m pytest tests/ -v

# Git status
git status
```

## Next Steps
1. Read AGENTS.md for full configuration
2. Test with sample documents
3. Customize for your specific use case
4. Commit changes frequently

---
Generated by instantiate_template.py
"""

    with open(checklist_file, 'w') as f:
        f.write(checklist_content)

    print(f"  ✅ Created INITIALIZATION_CHECKLIST.md")

    # Summary
    print("\n" + "=" * 60)
    print("✅ Template instantiation complete")
    print("\nNext steps:")
    print(f"  cd {target_path}")
    print(f"  cat INITIALIZATION_CHECKLIST.md")
    print(f"  python3 scripts/health_check.py --verbose")

    return True


def check_instantiation(target_dir: str) -> bool:
    """Check if instantiation was successful

    Args:
        target_dir: Target directory to check

    Returns:
        True if valid instantiation
    """
    target_path = Path(target_dir).expanduser()

    print("Instantiation Check")
    print("=" * 60)
    print(f"\nDirectory: {target_path}")

    checks = []

    # Check 1: Directory exists
    if target_path.exists():
        checks.append(("Directory exists", True))
    else:
        checks.append(("Directory exists", False))
        print("\n❌ Directory does not exist")
        return False

    # Check 2: .aget/version.json exists and valid
    version_file = target_path / '.aget' / 'version.json'
    if version_file.exists():
        try:
            with open(version_file) as f:
                version_data = json.load(f)

            required_fields = ['agent_name', 'aget_version', 'instance_type', 'created_at']
            if all(field in version_data for field in required_fields):
                checks.append(("version.json valid", True))
            else:
                checks.append(("version.json valid", False))
        except:
            checks.append(("version.json valid", False))
    else:
        checks.append(("version.json exists", False))

    # Check 3: Source code exists
    src_dir = target_path / 'src'
    if src_dir.exists() and src_dir.is_dir():
        checks.append(("Source code present", True))
    else:
        checks.append(("Source code present", False))

    # Check 4: Scripts exist
    scripts_dir = target_path / 'scripts'
    if scripts_dir.exists() and scripts_dir.is_dir():
        script_count = len(list(scripts_dir.glob('*.py')))
        checks.append((f"Scripts present ({script_count})", script_count >= 10))
    else:
        checks.append(("Scripts present", False))

    # Check 5: Tests exist
    tests_dir = target_path / 'tests'
    if tests_dir.exists() and tests_dir.is_dir():
        test_count = len(list(tests_dir.glob('test_*.py')))
        checks.append((f"Tests present ({test_count})", test_count >= 5))
    else:
        checks.append(("Tests present", False))

    # Display results
    print("\nChecks:")
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")

    all_passed = all(passed for _, passed in checks)

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ Instantiation valid")
    else:
        print("❌ Instantiation incomplete or invalid")

    return all_passed


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Helper tool to instantiate template for new agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Instantiate template
  python3 .aget/tools/instantiate_template.py invoice-processor ~/github/invoice-processor-AGET

  # Check instantiation
  python3 .aget/tools/instantiate_template.py --check ~/github/invoice-processor-AGET
        """
    )

    parser.add_argument(
        'agent_name',
        nargs='?',
        help='Name of new agent (e.g., invoice-processor)'
    )

    parser.add_argument(
        'target_dir',
        nargs='?',
        help='Target directory for new agent'
    )

    parser.add_argument(
        '--check',
        metavar='DIR',
        help='Check if instantiation was successful'
    )

    parser.add_argument(
        '--template-dir',
        metavar='DIR',
        help='Template directory (default: current directory)'
    )

    args = parser.parse_args()

    # Execute
    try:
        if args.check:
            success = check_instantiation(args.check)
            sys.exit(0 if success else 1)

        elif args.agent_name and args.target_dir:
            success = instantiate_template(
                args.agent_name,
                args.target_dir,
                template_dir=args.template_dir
            )
            sys.exit(0 if success else 1)

        else:
            parser.print_help()
            print("\nError: Must provide agent_name and target_dir, or --check")
            sys.exit(1)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
