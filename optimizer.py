"""
A lightweight heuristic optimization algorithm for a mini project.

Students are grouped by subject and then interleaved in round-robin order.
This reduces consecutive same-subject assignments in the generated seat list.
This is an optimization heuristic, not a machine-learning model.
"""


def optimize_seating(students, halls):
    seats = []

    for hall in halls:
        for seat_number in range(1, hall["capacity"] + 1):
            seats.append({
                "hall_id": hall["id"],
                "seat_number": seat_number
            })

    subject_groups = {}
    for student in students:
        subject_key = student["subject"].strip().lower()
        subject_groups.setdefault(subject_key, []).append(student)

    for group in subject_groups.values():
        group.sort(key=lambda student: student["student_no"])

    subject_keys = sorted(subject_groups)
    ordered_students = []

    while any(subject_groups.values()):
        for subject in subject_keys:
            if subject_groups[subject]:
                ordered_students.append(subject_groups[subject].pop(0))

    assignments = []
    for seat, student in zip(seats, ordered_students):
        assignments.append({
            "student_id": student["id"],
            "hall_id": seat["hall_id"],
            "seat_no": seat["seat_number"]
        })

    return assignments
