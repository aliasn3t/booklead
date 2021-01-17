import os
import shutil
import stat
import sys
import tempfile
import uuid
from multiprocessing import Process
from pathlib import Path

import pygit2

git_url = 'https://github.com/zencd/booklead'
git_branch = 'master'

app_dir = str(Path(__file__).parent.parent)
version_log_file = os.path.join(app_dir, 'history.txt')
do_hard_reset = int(os.getenv('DO_HARD_RESET', '0'))


def _git_clone_impl(url, repo_dir_tmp, branch):
    """This method must be global"""
    pygit2.clone_repository(url, repo_dir_tmp, checkout_branch=branch)


def git_clone(url, repo_dir, branch):
    """В новом процессе потому что pygit2 clone_repository оставляет файлы открытыми"""
    p = Process(target=_git_clone_impl, args=(url, repo_dir, branch))
    p.start()
    p.join()
    if p.exitcode != 0:
        print(f'git clone failed, code {p.exitcode}')
        sys.exit(1)


def git_pull(repo: pygit2.Repository, remote_name="origin"):
    """
    https://github.com/MichaelBoselowitz/pygit2-examples/blob/68e889e50a592d30ab4105a2e7b9f28fac7324c8/examples.py
    """
    branch = repo.head.shorthand
    for remote in repo.remotes:
        if remote.name == remote_name:
            remote.fetch()
            remote_master_id = repo.lookup_reference(f"refs/remotes/origin/{branch}").target
            merge_result, _ = repo.merge_analysis(remote_master_id)
            if merge_result & pygit2.GIT_MERGE_ANALYSIS_UP_TO_DATE:
                print('up to date')
                # Up to date, do nothing
                return False
            elif merge_result & pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD:
                # We can just fastforward
                print('fastforward')
                repo.checkout_tree(repo.get(remote_master_id))
                master_ref = repo.lookup_reference(f"refs/heads/{branch}")
                master_ref.set_target(remote_master_id)
                repo.head.set_target(remote_master_id)
                return True
            elif merge_result & pygit2.GIT_MERGE_ANALYSIS_NORMAL:
                raise Exception("Pulling remote changes leads to a conflict")
            else:
                raise AssertionError("Unknown merge analysis result")
    raise Exception(f'No remote found: {remote_name}')


def git_hard_reset(repo: pygit2.Repository):
    # If some local file has been altered the following pull may fail.
    # So let's discard all possible changes.
    # This is applicable for an end user windows distribution,
    #  but unacceptable during development, so there is an `if`.
    repo.reset(repo.head.target, pygit2.GIT_RESET_HARD)


def load_local_history(history_file):
    if os.path.exists(history_file):
        with open(history_file, 'r') as fd:
            return [line.strip() for line in fd]
    return []


def print_history_diff(history_before, history_after):
    diff = [x for x in history_after if x and x not in history_before]
    if diff:
        print('What is new:')
        for line in diff:
            print(line)


def get_remote_url(repo: pygit2.Repository):
    for remote in repo.remotes:
        if remote.name == 'origin':
            return remote.url
    return None


def ensure_git_dir():
    local_git = os.path.join(app_dir, '.git')
    if not os.path.exists(local_git):
        tmp_repo_dir = os.path.join(tempfile.gettempdir(), uuid.uuid4().hex)
        git_clone(git_url, tmp_repo_dir, git_branch)
        tmp_git = os.path.join(tmp_repo_dir, '.git')
        shutil.move(tmp_git, app_dir)


def rmtree(dir_):
    def onerror(func, path, exc_info):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    if os.path.exists(dir_):
        shutil.rmtree(dir_, onerror=onerror)


def main():
    ensure_git_dir()
    history_before = load_local_history(version_log_file)
    repo = pygit2.Repository(app_dir)
    url = get_remote_url(repo)
    print(f'Updating from {url} branch {repo.head.shorthand}')
    if do_hard_reset:
        print('Hard resetting...')
        git_hard_reset(repo)
    upd = git_pull(repo)
    if upd:
        print('Updated to the most recent version')
        history_after = load_local_history(version_log_file)
        print_history_diff(history_before, history_after)
    else:
        print('Already up to date')


if __name__ == '__main__':
    main()
