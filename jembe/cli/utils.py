import re
import os
import keyword
from jinja2 import Environment, FileSystemLoader, Template

__all__ = (
    "make_python_identifier",
    "extract_project_template",
)

# https://gist.github.com/JamesPHoughton/3a3f87c6662bf5c9eccc9f2206e228fd
def make_python_identifier(
    string, namespace=None, reserved_words=None, convert="drop", handle="force"
):
    """
    Takes an arbitrary string and creates a valid Python identifier.
    If the python identifier created is already in the namespace,
    or if the identifier is a reserved word in the reserved_words
    list, or is a python default reserved word,
    adds _1, or if _1 is in the namespace, _2, etc.
    Parameters
    ----------
    string : <basestring>
        The text to be converted into a valid python identifier
    namespace : <dictionary>
        Map of existing translations into python safe identifiers.
        This is to ensure that two strings are not translated into
        the same python identifier
    reserved_words : <list of strings>
        List of words that are reserved (because they have other meanings
        in this particular program, such as also being the names of
        libraries, etc.
    convert : <string>
        Tells the function what to do with characters that are not
        valid in python identifiers
        - 'hex' implies that they will be converted to their hexidecimal
                representation. This is handy if you have variables that
                have a lot of reserved characters
        - 'drop' implies that they will just be dropped altogether
    handle : <string>
        Tells the function how to deal with namespace conflicts
        - 'force' will create a representation which is not in conflict
                  by appending _n to the resulting variable where n is
                  the lowest number necessary to avoid a conflict
        - 'throw' will raise an exception
    Returns
    -------
    identifier : <string>
        A vaild python identifier based on the input string

    Examples
    --------
    >>> make_python_identifier('Capital')
    ('capital', {'Capital': 'capital'})
    >>> make_python_identifier('multiple words')
    ('multiple_words', {'multiple words': 'multiple_words'})
    >>> make_python_identifier('multiple     spaces')
    ('multiple_spaces', {'multiple     spaces': 'multiple_spaces'})
    When the name is a python keyword, add '_1' to differentiate it
    >>> make_python_identifier('for')
    ('for_1', {'for': 'for_1'})
    Remove leading and trailing whitespace
    >>> make_python_identifier('  whitespace  ')
    ('whitespace', {'  whitespace  ': 'whitespace'})
    Remove most special characters outright:
    >>> make_python_identifier('H@t tr!ck')
    ('ht_trck', {'H@t tr!ck': 'ht_trck'})
    Replace special characters with their hex representations
    >>> make_python_identifier('H@t tr!ck', convert='hex')
    ('h40t_tr21ck', {'H@t tr!ck': 'h40t_tr21ck'})
    remove leading digits
    >>> make_python_identifier('123abc')
    ('abc', {'123abc': 'abc'})
    namespace conflicts
    >>> make_python_identifier('Variable$', namespace={'Variable@':'variable'})
    ('variable_1', {'Variable@': 'variable', 'Variable$': 'variable_1'})
    >>> make_python_identifier('Variable$', namespace={'Variable@':'variable', 'Variable%':'variable_1'})
    ('variable_2', {'Variable@': 'variable', 'Variable%': 'variable_1', 'Variable$': 'variable_2'})
    throw exception instead
    >>> make_python_identifier('Variable$', namespace={'Variable@':'variable'}, handle='throw')
    Traceback (most recent call last):
     ...
    NameError: variable already exists in namespace or is a reserved word
    References
    ----------
    Identifiers must follow the convention outlined here:
        https://docs.python.org/2/reference/lexical_analysis.html#identifiers
    """

    if namespace is None:
        namespace = {}

    if reserved_words is None:
        reserved_words = []

    # create a working copy (and make it lowercase, while we're at it)
    s = string.lower()

    # remove leading and trailing whitespace
    s = s.strip()

    # Make spaces into underscores
    s = re.sub("[\\s\\t\\n]+", "_", s)
    s = re.sub("[-]+", "_", s)

    if convert == "hex":
        # Convert invalid characters to hex
        s = "".join(
            [c.encode("hex") if re.findall("[^0-9a-zA-Z_]", c) else c for c in s]
        )

    elif convert == "drop":
        # Remove invalid characters
        s = re.sub("[^0-9a-zA-Z_]", "", s)

    # Remove leading characters until we find a letter or underscore
    s = re.sub("^[^a-zA-Z_]+", "", s)

    # Check that the string is not a python identifier
    while s in keyword.kwlist or s in namespace.values() or s in reserved_words:
        if handle == "throw":
            raise NameError(s + " already exists in namespace or is a reserved word")
        if handle == "force":
            if re.match(".*?_\d+$", s):
                i = re.match(".*?_(\d+)$", s).groups()[0]
                s = s.strip("_" + i) + "_" + str(int(i) + 1)
            else:
                s += "_1"

    namespace[string] = s

    return s


def extract_project_template(name: str, ctx: dict):
    import jembe

    # obtain destination dir and template_dir
    dest = os.getcwd()
    template_dir = os.path.join(
        jembe.__path__[0], "cli", "project_templates", name  # type:ignore
    )
    env = Environment(autoescape=False, loader=FileSystemLoader(template_dir))
    # recursivly copy all files and directories from temple_dir to current_dir
    for root, dirs, files in os.walk(template_dir):
        rel_root = Template(os.path.relpath(root, template_dir)).render(ctx)
        for name in dirs:
            # run dir name throught jinja2 template
            dname = Template(name).render(ctx)

            try:
                os.mkdir(os.path.join(dest, rel_root, dname))
            except FileExistsError:
                pass
        for name in files:
            # run file name throught jinja2 template
            dname = Template(name).render(ctx)
            # remove .jpt file extension,
            dname = dname[:-4] if dname.endswith(".jpt") else dname

            # run files thought jinja2 template with ctx
            st = env.get_template(
                os.path.relpath(os.path.join(root, name), template_dir)
            )
            with open(os.path.join(dest, rel_root, dname), "w") as df:
                df.write(st.render(ctx))
