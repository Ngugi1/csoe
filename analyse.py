# Load repos
# Get first and last commit
# Split the timestamps into 10 periods
# Get LOC of c in P
# Get complexity
from datetime import datetime
from pydriller import RepositoryMining
import re

#  java file regex
java_file_regex = re.compile("")

# Repositories and their main branches
repos = [("aries", "trunk")]

# Prepare repo for mining
def configRepo(repo, reversed=None, 
                start=None,
                end=None,
                file_types=[".java"]):
    # Mine the main branch and only look for commits
    # for java files
    name, branch = repo
    return RepositoryMining(name, 
                            only_in_branch = branch, 
                            only_modifications_with_file_types=file_types, 
                            reversed_order=reversed, 
                            since=start, 
                            to=end)


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
def updateNumberOfDevs(dictionary, key, developer):
    # No. of developers is at index 3
    if keyExists(dictionary,key):
        dictionary[key][3].add(developer)
        return dictionary[key][3]
    else:
        return {developer}
#  Update number of changes 
def updateNumberOfFileChanges(dictionary, key):
    # Number of changes  is at index 2 
    if keyExists(dictionary, key):
        return dictionary[key][2] + 1
    else:
        return 0

#  does a key exist in th e dictionary?
def keyExists(dictionary, key):
    if key in dictionary:
        return True
    else:
        return False
# Calculate all metrics for a given time period
def processTimePeriod(period):
    # Period : (start_period, end_period)
    start,end = period
    # Metrics is a dictionary to keep track of metrics for this period
    metrics = {}
    # total changes over this period
    total_changes = 0
    # Initially, total changes is 0 
    # Traverse all commits in the time period
    for commit in traverse(configRepo(repo, start=unixTimestampToDate(start), end=unixTimestampToDate(end))):
        # Find all modifications
        for modification in commit.modifications:
            # Update the metrics
            if(getFileName(modification).endswith('.java')):
                total_changes += 1
                metrics[getFileName(modification)] = [getLinesOfCode(modification), 
                                                      getComplexity(modification),
                                                      updateNumberOfFileChanges(metrics,getFileName(modification)),
                                                      updateNumberOfDevs(metrics,getFileName(modification), commit.author.email),
                                                      total_changes]
    #  Compute entropy of changes - probability that the file will change
    for filename in metrics:
        # Add entropy for every file
        metrics[filename][3] = len(metrics[filename][3])
        print(metrics[filename][3])
        metrics[filename][4] = float(format(metrics[filename][2] / total_changes, ".6f"))
    print(metrics)
# Process all repos
for repo in repos:
    start, end = getRepoLife(configRepo(repo), configRepo(repo, reversed=True))
    for period in splitTimePeriods(int(start.strftime("%s")),int(end.strftime("%s")),3):
        # Basic metrics for a period
        processTimePeriod(period)

