from optparse import make_option
from django.core.management.base import BaseCommand
from student.models import CourseEnrollment
from django.contrib.auth.models import User
from shoppingcart.models import CertificateItem, DoesNotExist


class Command(BaseCommand):
    help = """
    This command takes two course ids as input and transfers
    all students enrolled in one course into the other.  This will
    remove them from the first class and enroll them in the second
    class in the same mode as the first one. eg. honor, verified,
    audit.

    example:
        # Transfer students from the old demoX class to a new one.
        manage.py ... transfer_students -f edX/Open_DemoX/edx_demo_course -t edX/Open_DemoX/new_demoX
    """

    option_list = BaseCommand.option_list + (
        make_option('-f', '--from',
                    metavar='SOURCE_COURSE',
                    dest='source_course',
                    help='The course to transfer students from.'),
        make_option('-t', '--to',
                    metavar='DEST_COURSE',
                    dest='dest_course',
                    help='The new course to enroll the student into.'),
    )

    def handle(self, *args, **options):
        source = options['source_course']
        dest = options['dest_course']

        source_students = User.objects.filter(courseenrollment__course_id=source)
        source_students = source_students.filter(courseenrollment__is_active=True)

        for user in source_students:
            # Find the old enrollment.
            enrollment = CourseEnrollment.objects.get(user=user, course_id=source)
            # Move the Student between the classes.
            mode = enrollment.mode
            CourseEnrollment.unenroll(user,source)
            CourseEnrollment.enroll(user, dest, mode=mode)

            if mode == 'verified':
                try:
                    certificate_item = CertificateItem.objects.get(course_id=source,
                        course_enrollment=enrollment)
                except DoesNotExist as e:
                    continue

                new_enrollment = CourseEnrollment.objects.get(user=user,
                    course_id=dest)

                certificate_item.course_id = dest
                certificate_item.course_enrollment = new_enrollment
                certificate_item.save()
