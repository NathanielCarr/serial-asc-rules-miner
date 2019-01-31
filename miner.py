import itertools
import time

FREQ_THRES = 100

class Rule:
    def __init__(self, left, right, all_freq, left_freq):
        self.left = left
        self.right = right
        self.all_freq = all_freq
        self.left_freq = left_freq

    def _cmp(self, other):
        conf_difference = self.confidence() - other.confidence()
        if conf_difference < 0:
            return -1
        elif conf_difference > 0:
            return 1
        else:
            self_string = " ".join(self.left)
            other_string = " ".join(other.left)
            if self_string > other_string:
                return -1
            elif self_string < other_string:
                return 1
        return 0

    def __lt__(self, other):
        return self._cmp(other) < 0

    def __le__(self, other):
        return self._cmp(other) <= 0

    def __eq__(self, other):
        return self._cmp(other) == 0

    def __str__(self):
        return "{" + ", ".join(self.left) + "} -> {" + ", ".join(self.right) + "} - frequency: " + str(self.all_freq) + ", confidence = " + str(self.confidence())

    def confidence(self):
        return self.all_freq/self.left_freq


def prune(candidates):
    '''
    -----------------------------------------------------------------
    This function creates a dict with all keys from the candidates
    dict removed if their value did not meet or exceed FREQ_THRES.
    -----------------------------------------------------------------
    Parameters:
        - candidates: a dict whose keys are the itemsets, delimited 
            by a space. The value at the key is the frequency of 
            the itemset.
    Returns:
        - A dict with all infrequent itemsets removed.
    -----------------------------------------------------------------
    '''

    return {item: candidates[item] for item in candidates if candidates[item] >= FREQ_THRES}


def make_candidates(prev_frequents):
    '''
    -----------------------------------------------------------------
    This function generates all possible candidates one level higher
    than the level of prev_frequents. For example, if prev_frequents is a dict
    of itemsets of size 2, then the result will be a dict of itemsets
    of size 3. Candidates are generated by the k-1 X k-1 prefix condition.
    -----------------------------------------------------------------
    Parameters:
        - prev_frequents: a dict whose keys are the itemsets for the 
            level once below the level whose candidates are being
            created, delimited by a space (for example, if we are 
            looking for 3-itemset candidates, the keys will be 
            pairs delimited by a space). The value at the key
            is the frequency of the itemset.
    Returns:
        - A dict of all the new candidate itemsets, with frequency
            set to 0 for each.
    -----------------------------------------------------------------
    '''

    candidates = {}
    freq_list = sorted(list(prev_frequents))

    # iterate through outer list, then inner list to form all possible candidates.
    for outer in range(0, len(freq_list)):
        outer_items = freq_list[outer].split()
        prefix = len(outer_items) - 1

        # iterate through inner list.
        for inner in range(outer, len(freq_list)):
            inner_items = freq_list[inner].split()

            # check for common prefix.
            i = 0
            while i < prefix and i < len(outer_items) and i < len(inner_items) and outer_items[i] == inner_items[i]:
                i += 1

            # validate according to k-1 X k-1 candidate generation rule.
            if i == prefix:
                candidates[" ".join(outer_items + [inner_items[prefix]])] = 0

    return candidates


def make_rules(top_level, *args):
    '''
    -----------------------------------------------------------------
    This function is responsible for creating Rules for a 
    given level (for example, pair rules or triple rules).
    -----------------------------------------------------------------
    Parameters:
        - top_level: a dict whose keys are the itemsets for the level
            whose Rules are being calculated, delimited by a space 
            (for example, if we are looking for pair rules, the keys 
            will be pairs delimited by a space). The value at the key
            is the frequency of the itemset.
        - args: dicts at the levels below top_level, starting with
            itemsets of size 1, then itemsets of size 2, and so on.
    Returns:
        - A list of all Rules found on the current level.
    -----------------------------------------------------------------
    '''
    level_rules = []  # hold Rules.

    # the top_level is a dict of itemsets.
    for itemset in top_level:
        items = itemset.split()  # separate the items.

        # form all combinations of the items with at least one item included
        # and at least one item excluded using itertools (default Python library).
        combinations = []
        for i in range(1, len(items)):
            combinations += list(map(list, itertools.combinations(items, i)))

        # for each combination previously found, they will make up the left side of the Rule
        # and the items exclusded from the combination found will make up the right side.
        # The frequency of finding all items in the rules together is already found inside
        # top_level, but the frequency of finding all items in the left together can be found
        # in args.
        for combination in combinations:
            other = [item for item in items if item not in combination]
            level_rules.append(Rule(combination, other, top_level[itemset], args[len(
                combination) - 1][" ".join(combination)]))

    return level_rules

browsing_path = input("Please enter the path to the browsing file: ")
log_path = input("Please enter the path to the logging file: ")

try:
    start_time = time.time()

    # read in all lines from the database.
    lines = []
    with open(browsing_path) as browsing:
        lines = list(map(lambda line: sorted(line.strip().split()), browsing.readlines()))

    # gather candidate singles and count their frequencies by searching the database.
    singles = {}
    for line in lines:
        for item in line:
            if item not in singles:
                singles[item] = 0
            singles[item] += 1

    # prune candidate singles
    singles = prune(singles)

    # gather candidate pairs from frequent singles.
    pairs = make_candidates(singles)

    # count frequencies for candidate pairs by searching the database.
    for line in lines:
        combinations = itertools.combinations(line, 2)
        for combination in combinations:
            if (" ".join(combination)) in pairs:
                pairs[" ".join(combination)] += 1

    # prune candidate pairs.
    pairs = prune(pairs)

    # gather pair rules.
    pair_rules = sorted(make_rules(pairs, singles), reverse=True)

    # gather candidate triples.
    triples = make_candidates(pairs)

    # count frequencies for candidate triples by searching the database.
    for line in lines:
        combinations = itertools.combinations(line, 3)
        for combination in combinations:
            if (" ".join(combination)) in triples:
                triples[" ".join(combination)] += 1

    # prune candidate triples.
    triples = prune(triples)

    # gather triple rules.
    triple_rules = sorted(make_rules(triples, singles, pairs), reverse=True)

    end_time = time.time()

    # clear log file, then write discovered rules.
    with open(log_path, "w") as log:
        log.writelines("")
    with open(log_path, "a") as log:
        log.writelines("\nFound " + str(len(pair_rules)) + " pair rules from " + str(len(pairs)) + " frequent pairs:\n")
        for rule in pair_rules:
            log.writelines(str(rule) + "\n")

        log.writelines("\nFound " + str(len(triple_rules)) + " triple rules from " + str(len(triples)) + " frequent triples:\n")
        for rule in triple_rules:
            log.writelines(str(rule) + "\n")

        log.writelines("Found " + str(len(singles)) + " frequent singles:\n")
        for itemset in sorted(list(singles)):
            log.writelines(itemset + ": " + str(singles[itemset]) + "\n")

        log.writelines("Found " + str(len(pairs)) + " frequent pairs:\n")
        for itemset in sorted(list(pairs)):
            log.writelines(itemset + ": " + str(pairs[itemset]) + "\n")

        log.writelines("Found " + str(len(triples)) + " frequent triples:\n")
        for itemset in sorted(list(triples)):
            log.writelines(itemset + ": " + str(triples[itemset]) + "\n")

    print("\nRule discovery completed in " + "{0:.2f}".format(time.time() - start_time) + " seconds. Check the selected logging file for details.")

except BaseException as e:
    print("Error occurred: " + str(e))
