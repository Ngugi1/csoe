# Load repos
# Get first and last commit
# Split the timestamps into 10 periods
# Get LOC of c in P
# Get complexity
from datetime import datetime
from pydriller import RepositoryMining, GitRepository
import re


# Repositories and their main branches
repos = [("aries", "trunk")]


# Prepare repo for mining
def configure_repo(repository,
                   reverse=None,
                   repo_start=None,
                   repo_end=None,
                   file_types=[".java"]):
    # Mine the main branch and only look for commits
    # for java files
    name, branch = repository
    return RepositoryMining(name, 
                            only_in_branch=branch,
                            only_modifications_with_file_types=file_types, 
                            reversed_order=reverse,
                            since=repo_start,
                            to=repo_end)


# Traverse repo commits
def traverse(repository):
    return repository.traverse_commits()


# Initialize GitRepository
def init_git_repo(path):
    return GitRepository(path)


# Given a unix timestamp, give back a date
def unix_timestamp_to_date(timestamp):
    return datetime.fromtimestamp(timestamp)


# Given a date, convert to unix timestamp
def date_string_to_timestamp(date):
    return int(date.strftime("%s"))


# Get Bug Inducing Commits
def get_bug_inducing_commits(git_repo, current_commit, current_modification, current_period):
    current_period_start, current_period_end = current_period
    bic = []
    working_repo = init_git_repo(git_repo)
    # Get bug introducing changes only within this time period
    for commit_list in \
            list(working_repo.get_commits_last_modified_lines(
                commit=current_commit,
                modification=current_modification).values()):
        for commit_hash in commit_list:
            bug_inducing_commit = working_repo.get_commit(commit_hash)
            commit_date = bug_inducing_commit.committer_date
            if date_string_to_timestamp(commit_date) >= current_period_start and \
                    (date_string_to_timestamp(commit_date) <= current_period_end):
                bic.append(bug_inducing_commit)
    return bic


# get the initial and last commit dates
# These will be used to split the time into periods
def get_repo_life(chronological, reversed_chronological):
    # Traverse chronological
    commits = traverse(chronological)
    # Traverse reversed repo
    reversed_commits = traverse(reversed_chronological)
    # Get initial commit
    initial_commit = next(commits)
    # Get the last commit
    last_commit = next(reversed_commits)
    return initial_commit.author_date, last_commit.author_date


# Given the project lifetime, split it into portions defined by 
# period length
def split_time_periods(project_start, project_end, period_length_months):
    # convert months to seconds
    period_length_in_secs = 86400 * 30 * period_length_months
    time_periods = []
    #  consider only full time periods - don't analyse the remainder
    while project_start <= project_end:
        time_periods.append((project_start, project_start + period_length_in_secs))
        # Add a second to the border periods to avoid overlapping of analysis
        project_start += period_length_in_secs + 1
    return time_periods


# Get lines of code for all files
def get_lines_of_code(modification):
    # modification : Modification
    return modification.nloc


# Get the cyclomatic complexity 
def get_complexity(modification):
    # commit : CommitObject
    return modification.complexity


# Get the filename
def get_file_name(modification):
    return modification.filename


def update_number_of_developers(dictionary, key, developer):
    # No. of developers is at index 3
    if key_exists(dictionary, key):
        print(dictionary[key][3])
        dictionary[key][3].add(developer)
        return dictionary[key][3]
    else:
        return {developer}


#  Update number of changes 
def update_number_of_file_changes(dictionary, key):
    # Number of changes  is at index 2 
    if key_exists(dictionary, key):
        return dictionary[key][2] + 1
    else:
        return 0


#  does a key exist in th e dictionary?
def key_exists(dictionary, key):
    if key in dictionary:
        return True
    else:
        return False


# Commit message Regex
fixed_regex = re.compile(r'fix(e[ds])?[ \t]*(for)[ ]*?(bugs?)?(defects?)?(pr)?[# \t]*')
patched_regex = re.compile(r'patch(ed)?[ \t]*(for)[ ]*?(bugs?)?(defects?)?(pr)?[# \t]*')
bugs_regex = re.compile(r'(\sbugs?\s|\spr\s|\sshow_bug\.cgi\?id=)[# \t]*')


# check if a commit is fixing a bug
def is_bug_fixing_commit(commit):
    if fixed_regex.search(commit.msg) or \
            patched_regex.search(commit.msg) or \
            bugs_regex.search(commit.msg):
        print(commit.msg)
        return True
    else:
        return False


# Set past faults
def set_past_faults(p_faults, filename):
    if key_exists(p_faults, filename):
        return p_faults[filename]
    else:
        return 0


# Calculate all metrics for a given time period
def process_time_period(project_name, period, past_faults={}):
    # buffer for faults in this period, they will be used in the next time period
    # as past faults
    current_faults = {}
    # Period : (start_period, end_period)
    start_period, end_period = period
    # Metrics is a dictionary to keep track of metrics for this period
    metrics = {}
    # total changes over this period
    total_changes = 0
    # Traverse all commits in the time period
    for commit_c in traverse(configure_repo(repo, repo_start=unix_timestamp_to_date(start_period),
                                            repo_end=unix_timestamp_to_date(end_period))):

        # Find all modifications
        for modification in commit_c.modifications:
            # Update the metrics
            if get_file_name(modification).endswith('.java') and modification.change_type.name != "DELETE"\
                    and modification.change_type.name != "RENAME":
                print("----mmmmmmmmmmmmmmmmmm-----")
                print(modification.change_type.name)
                print("----mmmmmmmmmmmmmmmmmm-----")
                total_changes += 1
                metrics[get_file_name(modification)] = [get_lines_of_code(modification),
                                                        get_complexity(modification),
                                                        update_number_of_file_changes(metrics,
                                                                                      get_file_name(modification)),
                                                        update_number_of_developers(metrics,
                                                                                    get_file_name(modification),
                                                                                    commit_c.author.email
                                                                                    # Developer count
                                                                                    ),
                                                        total_changes,  # Total changes
                                                        set_past_faults(past_faults, get_file_name(modification))]
        # Check if this commit is fixing a bug and find commits that introduced the bug
        if is_bug_fixing_commit(commit_c):
            for buggy_commit in get_bug_inducing_commits(project_name, commit_c, modification, period):
                for buggy_modification in buggy_commit.modifications:
                    # Increase the number of faults in this file
                    if key_exists(current_faults, get_file_name(buggy_modification)):
                        current_faults[get_file_name(buggy_modification)] = \
                            current_faults[get_file_name(buggy_modification)] + 1
                    else:
                        current_faults[get_file_name(buggy_modification)] = 1
    #                 Also mark the file as buggy if it is in our metrics
                    print("\n+++++++++++++++++++++++")
                    print(get_file_name(buggy_modification))
                    print("\n++++++++++++++++++++++++")
                    if get_file_name(modification).endswith('.java'):
                        if get_file_name(modification).endswith('.java') and \
                                key_exists(metrics, get_file_name(buggy_modification)):
                            metrics[get_file_name(buggy_modification)].append(1)
                        else:
                            metrics[get_file_name(modification)] = [0, 0, 0, set(), 0, 0, 1]

    #  Compute entropy of changes - probability that the file will change
    for filename in metrics:
        # Add entropy for every file
        metrics[filename][3] = len(metrics[filename][3])
        metrics[filename][4] = float(format(metrics[filename][2] / total_changes, ".6f"))

    print(metrics)


# Process all repos
for repo in repos:
    start, end = get_repo_life(configure_repo(repo), configure_repo(repo, reverse=True))
    for p_period in split_time_periods(int(start.strftime("%s")), int(end.strftime("%s")), 3):
        # Basic metrics for a period
        repo_name, _ = repo
        process_time_period(repo_name, p_period)
        exit()

