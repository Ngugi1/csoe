# Load repos
# Get first and last commit
# Split the timestamps into 10 periods
# Get LOC of c in P
# Get complexity
from datetime import datetime
from pydriller import RepositoryMining
# Repositories and their main branches
repos = [("aries", "trunk"), 
                ("falcon", "master"), 
                ("ranger","master"),
                ("sqoop", "trunk"),
                ("whirr", "trunk")]
commit_type = ".java"


# Prepare repo for mining
def configRepo(repo, reversed=None, start=None,end=None):
    # Mine the main branch and only look for commits
    # for java files
    name, branch = repo
    return RepositoryMining(name, 
                            only_in_branch = branch, 
                            only_modifications_with_file_types= [commit_type], reversed_order=reversed, since=start, to=end)


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
# Given a unix timestamp, give back a date
def unixTimestampToDate(timestamp):
    return datetime.fromtimestamp(timestamp)

#  Update number of changes 
def updateNumberOfChanges(dictionary, key):
    if keyExists(dictionary, key):
        return dictionary[key][2] + 1
    else:
        return 0
#  does a key exist in th e dictionary?
def keyExists(dictionary, key):
    key in dictionary
# Calculate all metrics for a given time period
def processTimePeriod(period):
    # Period : (start_period, end_period)
    start,end = period
    # Metrics is a dictionary to keep track of metrics for this period
    metrics = {}
    # Traverse all commits in the time period
    for commit in traverse(configRepo(repo, start=unixTimestampToDate(start), end=unixTimestampToDate(end))):
        # Find all modifications
        for modification in commit.modifications:
            # Uopdate the metrics
            metrics[getFileName(modification)] = [getLinesOfCode(modification), 
                                                    getComplexity(modification),
                                                    # If the file is not added already, then this is the first time it was added
                                                   updateNumberOfChanges(metrics,getFileName(modification))]
    
    print(metrics)


# Process all repos
for repo in repos:
    start, end = getRepoLife(configRepo(repo), configRepo(repo, reversed=True))
    for period in splitTimePeriods(int(start.strftime("%s")),int(end.strftime("%s")),3):
        processTimePeriod(period)

