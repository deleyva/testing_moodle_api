import moodle_api as mp

mp.call(
    "core_course_create_categories",
    categories=[
        {
            "name": "Categoría Jesús",
            "parent": 1,
        },
    ],
)
