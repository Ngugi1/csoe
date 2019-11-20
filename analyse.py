# Load repos
# Get first and last commit
# Split the timestamps into 10 periods
# Get LOC of c in P
# Get complexity
from time import time
from pydriller import RepositoryMining
# Repositories and their main branches
repos = [("aries", "trunk"), 
                ("falcon", "master"), 
                ("ranger","master"),
                ("sqoop", "trunk"),
                ("whirr", "trunk")]
commit_type = ".java"


# Prepare repo for mining
def configRepo(repo, reversed=None):
    # Mine the main branch and only look for commits
    # for java files
    name, branch = repo
    return RepositoryMining(name, 
                            only_in_branch = branch, 
                            only_modifications_with_file_types= [commit_type], reversed_order=reversed)


# Traverse repo commits
def traverse(repo):
    return repo.traverse_commits()
# get the inital and last commit dates
# These will be used to split the time into periods
def getRepoLife(chronological, reversed_chronological):
    # Traverse chronological
    commits = traverse(chronological)
    # Traverse reversed repo
    reversed_commits = traverse(reversed_chronological)
    # Get initial commit
    initialcommit = next(commits)
    # Get the last commit
    lastcommit = next(reversed_commits)
    return (initialcommit.author_date, lastcommit.author_date)
    # return (initialcommit.author_date.strftime("%s"), lastcommit.author_date.strftime("%s"))
# Given the project lifetime, split it into portions defined by 
# period length
def splitTimePeriods(project_start, project_end, period_length_months):
    # convert months to seconds
    period_length_in_secs = 86400 * 30 * period_length_months
    time_periods = []
    #  consider only full time periods - don't analyse the remainder
    while(project_start <= project_end):
        time_periods.append((project_start, project_start + period_length_in_secs))
        # Add a second to the border periods to avoid overlapping of analysis
        project_start += period_length_in_secs + 1
    return time_periods

# Get lines of code for all files
def getLinesOfCode(modification):
    # modification : Modification
    return modification.nloc
# Get the cyclomatic complexity 
def getComplexity(modification):
    # commit : CommitObject
    return modification.complexity
# Get the filename
def getFileName(modification):
    return modification.filename




for repo in repos:
    for commit in configRepo(repo).traverse_commits():
        for modification in commit.modifications:
            print(getFileName(modification), getLinesOfCode(modification), getComplexity(modification))
    exit()
    start, end = getRepoLife(configRepo(repo), configRepo(repo, reversed=True))
    print("Start - {} ".format(start.strftime("%Y-%m-%d %H:%M:%S")))
    print("Start - {} ".format(end.strftime("%Y-%m-%d %H:%M:%S")))
    splits = splitTimePeriods(int(start.strftime("%s")), int(end.strftime("%s")), 3)
    
    print("\n")
    # print("Initial commit - {} and Last commit - {} \n".format(start, end))


