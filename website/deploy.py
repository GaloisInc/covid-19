#! /usr/bin/env python3

import click
import os
import shutil
import subprocess

_dir = os.path.dirname(os.path.abspath(__file__))

@click.command()
@click.option('--yes-to-all', is_flag=True, default=False, help='just say yes to all questions')
def main(yes_to_all):
    branch_last = _check_committed()
    if branch_last != 'master':
        raise ValueError(f"Cannot deploy from `{branch_last}`; change to `master`.")

    print('Building website...')
    subprocess.check_call(['./website-data.py'],
            cwd=os.path.dirname(_dir))
    subprocess.check_call(['npm', 'install', '--no-save'], cwd=_dir)
    subprocess.check_call(['npm', 'run', 'build'], cwd=_dir)

    # Get user confirmation before continuing.
    if not yes_to_all: 
        _check_proceed('Continuing will force-replace the `gh-pages` branch '
            'locally.')

    # Paranoid, but double check we're still on master and git state is clean.
    assert _check_committed() == 'master'

    # Create a new, orphaned, empty gh-pages branch
    print('Overwriting `gh-pages` branch')
    git_dir = os.path.dirname(_dir)
    git_cmd = lambda args: subprocess.check_output(args, cwd=git_dir).decode()

    gh_exists = git_cmd(['git', 'branch', '--list', 'gh-pages'])
    if gh_exists.strip():
        git_cmd(['git', 'branch', '-D', 'gh-pages'])
    git_cmd(['git', 'checkout', '--orphan', 'gh-pages'])
    git_cmd(['git', 'rm', '-rf', '.'])

    # Copy files + dirs from dist
    src_root = os.path.join(_dir, 'dist')
    dst_root = os.path.dirname(_dir)
    copied_list = []
    for f in os.listdir(src_root):
        assert f != 'website', 'This would cause issues -- duplicate name.'

        fpath = os.path.join(src_root, f)
        if os.path.isdir(fpath):
            shutil.copytree(fpath, os.path.join(dst_root, f))
        else:
            shutil.copy2(fpath, os.path.join(dst_root, f))
        copied_list.append(f)

    # GitHub pages need a .nojekyll file!!
    # E.g., https://github.com/zeit/next.js/issues/2029
    with open(os.path.join(dst_root, '.nojekyll'), 'w') as f:
        pass
    copied_list.append('.nojekyll')

    # Add files to be committed
    git_cmd(['git', 'add'] + copied_list)
    git_cmd(['git', 'commit', '-m', 'Website built'])

    git_cmd(['git', 'checkout', branch_last])

    print('Listing files in `gh-pages`')
    subprocess.check_call(['git', 'ls-tree', '--name-only', '-r', 'gh-pages'],
            cwd=git_dir)

    if not yes_to_all:
        _check_proceed('Does the above look correct?  Continuing will push '
            'local `gh-pages` to remote.')

    # Don't hide output, hence no git_cmd
    subprocess.check_call(['git', 'push', 'gh-origin', '--force',
            'gh-pages:gh-pages'])

    print('')
    print('')
    print('All done.  Navigate to https://galoisinc.github.io/covid-19-staging '
            '.  When satisfied, execute:\n\n  git push [public-remote] --force '
            'gh-pages:gh-pages\n  git push origin --force :gh-pages\n\nWhich '
            'both updates the production copy and removes the staging '
            'website.')


def _check_committed():
    """Ensure there are no uncommitted changes in git.
    """
    o = subprocess.check_output(['git', 'status', '--porcelain', '-b'],
            cwd=os.path.dirname(_dir))
    o = o.decode()

    branch_current = None
    for line in o.split('\n'):
        if line.startswith('## '):
            # Branch information... tracking information after ellipses.
            branch_current = line[3:].split('...', 1)[0].strip()
        elif line:
            raise ValueError(f'Uncommitted change: {line}\n\nDeploy requires a clean state in git.')

    return branch_current


def _check_proceed(msg):
    print(msg)
    print('')
    confirm = '!'
    while confirm not in ['y', 'n']:
        confirm = input('Are you sure you want to proceed?  (y/N) ')
    if confirm != 'y':
        print('Aborting.')
        raise SystemExit(1)


if __name__ == '__main__':
    # pylint: disable=no-value-for-parameter
    main()

