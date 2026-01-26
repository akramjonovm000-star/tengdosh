from django.utils import timezone

def calculate_score(attempt):
    score = 0
    for item in attempt.answers.all():
        if set(item.answers.all()) == set(item.question.answers.all()):
            item.is_correct = True
            score += 1
        else:
            item.is_correct = False
        item.save()

    attempt.is_completed = True
    attempt.closed_at = timezone.now()
    attempt.score = score
    attempt.save()

    return score
