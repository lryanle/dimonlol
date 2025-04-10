import sqlite3
import re
from urllib.parse import quote 

db_name = "search.db"


# Create table if one doesnt exist
def create_alias_table():
    try:
        with sqlite3.connect(db_name, check_same_thread=False) as con:
            cur = con.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS alias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alias TEXT NOT NULL,
                    pattern TEXT NOT NULL
                )
                """
            )
            return True, "Success"
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return False, f"An error occurred: {e}"
        
def get_tokens(search_text):
    return re.findall("(<\$[\d&]>)+", search_text)

def return_default(tokens=None):
    return f"https://www.google.com/search{'?q='+'+'.join(tokens) if tokens else ''}"

def _find_matching_alias(alias_results, token_count):
    for idx, tokens_len in enumerate([len(get_tokens(i[1])) for i in alias_results]):
        if token_count == tokens_len:
            return (alias_results[idx][1], alias_results[idx][2])
    return None

def verify_https(url):
    if "://" not in url:
        return "https://" + url
    return url

def verify_pattern(alias, pattern, update_id=None):
    con = sqlite3.connect(db_name, check_same_thread=False)
    cur = con.cursor()
    
    unsorted_pattern_tokens = get_tokens(pattern)
    pattern_tokens = sorted(unsorted_pattern_tokens)
    unsorted_alias_tokens = get_tokens(alias)
    alias_tokens = sorted(unsorted_alias_tokens)
    
    # Check if pattern and alias have equal number of tokens
    if len(pattern_tokens) != len(alias_tokens):
        return False, f"Alias '{alias}' and pattern '{pattern}' do not match. Expecting {abs(len(pattern_tokens) - len(alias_tokens))} more token(s)."
    
    # Check if each alias token matches each pattern token
    for k, token in enumerate(alias_tokens):
        if token not in pattern_tokens[k]:
            return False, f"Alias token '{token}' and pattern '{pattern_tokens[k]}' do not match. Please check your inputs."

    # get all aliases with the starter alias
    cur.execute("SELECT id, alias FROM alias WHERE alias LIKE ?", (alias.split(" ")[0] + "%",))
    similar_aliases = cur.fetchall()
    print(similar_aliases)
    similar_ids = [alias[0] for alias in similar_aliases]
    similar_aliases = [alias[1] for alias in similar_aliases]
    
    # ignore/remove previous alias from check if updating
    if (update_id is not None):
        print(update_id)
        print(similar_aliases)
        print(similar_ids)
        print(similar_ids.index(update_id))
        similar_aliases.remove(similar_aliases[similar_ids.index(update_id)])   
        print(similar_aliases) 
    
    # Check if alias already exists
    if similar_aliases.count(alias) > 0:
        return False, f"Alias '{alias}' already exists"
    
    
    if "<$&>" in pattern_tokens:
        # make sure the last token is <$&>
        if unsorted_pattern_tokens[-1] != "<$&>":
            return False, "The '<$&>' token must be at the end of the pattern. Please check your inputs."
        
        # make sure there are are only one <$&> token in the search pattern
        if pattern_tokens.count("<$&>") > 1:
            return False, "There can only be one '<$&>' token in a pattern. Please check your inputs."
        
        # make sure there arent any other aliases with the same token count
        new_set = [get_tokens(i) for i in similar_aliases]
        new_set.append(get_tokens(alias))
        new_set_len = [len(i) for i in new_set]
        
        if len(new_set_len) != len(set(new_set_len)):
            return False, f"There already exists an alias with {len(get_tokens(alias))} pattern tokens."
        
        # check if <$&> exist in more than 1 alias
        if len([i for i in new_set if "<$&>" in i]) > 1:
            return False, f"The '<$&>' token must be unique across all aliases. Please check all '{alias.split(' ')[0]}' aliases and determine where the '<$&>' token should be."

    return True, "Success"

def read_alias(search_text):
    try:
        tokens = search_text.strip().split()
        if not tokens:
            return return_default()

        con = sqlite3.connect(db_name, check_same_thread=False)
        cur = con.cursor()
        cur.execute("SELECT * FROM alias WHERE alias = ? OR alias LIKE ? || ' %'", (tokens[0], tokens[0]))
        alias_results = cur.fetchall()

        if not alias_results:
            return return_default(tokens)

        token_count = len(tokens[1:])
        alias = _find_matching_alias(alias_results, token_count)

        if alias is None:
            alias = [i for i in alias_results if "<$&>" in get_tokens(i[1]) and len(get_tokens(i[1])) > 0]
            if not alias:
                return return_default(tokens)
            alias = (alias[0][1], alias[0][2])
            

        return_str = alias[1]
        for k, v in enumerate(get_tokens(alias[1])):
            if v == "<$&>":
                return_str = return_str.replace(v, quote(" ".join(tokens[k+1:])))
                continue
            return_str = return_str.replace(v, tokens[k+1])

        return return_str

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return "https://www.google.com"
    finally:
        if 'con' in locals():
            con.close()

def get_all_aliases():
    try:
        with sqlite3.connect(db_name, check_same_thread=False) as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM alias")
            aliases = cur.fetchall()
            return [{"id": id, "alias": alias, "pattern": pattern} for id, alias, pattern in aliases]
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return False, []

def add_alias(alias, pattern):
    try:
        con = sqlite3.connect(db_name, check_same_thread=False)
        cur = con.cursor()
        
        success, message = verify_pattern(alias, pattern)
        print(success,message)
        if not success:
            return False, message

        cur.execute(
            "INSERT INTO alias (alias, pattern) VALUES (?, ?)",
            (alias, verify_https(pattern)),
        )
        con.commit()
        
        return True, "Success"
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return False, f"An error occurred: {e}"
    finally:
        con.close()


def remove_alias(alias):
    try:
        con = sqlite3.connect(db_name, check_same_thread=False)
        cur = con.cursor()
        
        cur.execute("DELETE FROM alias WHERE id = ?", (alias,))
        
        con.commit()
        return True, "Success"
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return False
    finally:
        con.close()


def update_alias(id, alias, pattern):
    try:
        con = sqlite3.connect(db_name, check_same_thread=False)
        cur = con.cursor()

        success, message = verify_pattern(alias, pattern, id)
        print(success,message)
        if not success:
            return False, message
    
        cur.execute('UPDATE alias SET alias = ?, pattern = ? WHERE id = ?', (alias, verify_https(pattern), id))
        con.commit()
        return True, "Success"
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return False
    finally:
        con.close()
