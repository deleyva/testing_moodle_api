from requests import post
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Module variables to connect to moodle api
KEY = os.getenv("AEDUCAR_API_KEY")
URL = os.getenv("AEDUCAR_API_URL")
ENDPOINT = "/webservice/rest/server.php"


def rest_api_parameters(in_args, prefix="", out_dict=None):
    """Transform dictionary/array structure to a flat dictionary, with key names
    defining the structure.
    Example usage:
    >>> rest_api_parameters({'courses':[{'id':1,'name': 'course1'}]})
    {'courses[0][id]':1,
     'courses[0][name]':'course1'}
    """
    if out_dict is None:
        out_dict = {}
    if type(in_args) not in (list, dict):
        out_dict[prefix] = in_args
        return out_dict
    prefix = prefix + "{0}" if prefix == "" else prefix + "[{0}]"
    if type(in_args) == list:
        for idx, item in enumerate(in_args):
            rest_api_parameters(item, prefix.format(idx), out_dict)
    elif type(in_args) == dict:
        for key, item in in_args.items():
            rest_api_parameters(item, prefix.format(key), out_dict)
    return out_dict


def call(fname, **kwargs):
    """Calls moodle API function with function name fname and keyword arguments.
    Example:
    >>> call_mdl_function('core_course_uate_courses',
                           courses = [{'id': 1, 'fullname': 'My favorite course'}])
    """
    parameters = rest_api_parameters(kwargs)
    parameters.update(
        {"wstoken": KEY, "moodlewsrestformat": "json", "wsfunction": fname}
    )
    response = post(URL + ENDPOINT, parameters).json()
    if type(response) == dict and response.get("exception"):
        raise SystemError("Error calling Moodle API\n", response)
    return response


class CourseList:
    """Class for list of all courses in Moodle and order them by id and idnumber."""

    def __init__(self):
        # TODO fullname atribute is filtered
        # (no <span class="multilang" lang="sl">)
        courses_data = call("core_course_get_courses")
        self.courses = [Course(**data) for data in courses_data]
        self.id_dict = {}
        self.idnumber_dict = {}
        for course in self.courses:
            self.id_dict[course.id] = course
            if course.idnumber:
                self.idnumber_dict[course.idnumber] = course

    def __getitem__(self, key):
        if 0 <= key < len(self.courses):
            return self.courses[key]
        else:
            raise IndexError

    def by_id(self, id):
        "Return course with given id."
        return self.id_dict.get(id)

    def by_idnumber(self, idnumber):
        "Course with given idnumber"
        return self.idnumber_dict.get(idnumber)

    def uate_courses(self, courses_to_uate, fields):
        "Uate a list of courses in one go."
        if "id" not in fields:
            fields.append("id")
        courses = [{k: c.__dict__[k] for k in fields} for c in courses_to_uate]
        return call("core_course_update_courses", courses=courses)


class Course:
    """Class for a single course.

    Example:
    >>> Course(name="Example course", shortname="example", categoryid=1, idnumber=123)
    """

    def __init__(self, **data):
        self.__dict__.update(data)

    def create(self):
        "Create this course on moodle"
        res = call("core_course_create_courses", courses=[self.__dict__])
        if type(res) == list:
            self.id = res[0].get("id")

    def update(self):
        "Update course"
        r = call("core_course_update_courses", courses=[self.__dict__])

    def i18n_set(self, **data):
        'Transform given field to multilang string with <span class="multilang"'
        template = '<span class="multilang" lang="{}">{}</span>'
        for field in data:
            value = data[field]
            if type(value) == dict:
                new_value = ""
                for lang in value:
                    if len(value) == 1:
                        new_value += value[lang]
                    elif value[lang]:
                        new_value += template.format(lang, value[lang])
                self.__dict__[field] = new_value
