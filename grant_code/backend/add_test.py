from pprint import pprint
from apps.application.models import Question, Answer
tests = []
with open("example.txt", "r", encoding="utf-8") as file:
    content = file.readlines()
    inx = -1
    ans = -1
    variants = []
    test = {}
    for line in content:
        if inx == -1:
            test["question"] = line.strip()
            inx += 1
        else:
            if line.strip().endswith(" *"):
                test["answer"] = inx
                variants.append(line.strip()[3:-2])
            else:
                variants.append(line.strip()[3:])
            inx += 1
            if inx == 4:
                inx = -1
                test["variants"] = variants
                tests.append(test)
                test = {}
                variants = []

for test in tests:
    question = Question.objects.create(text=test["question"])
    variants = [
        Answer.objects.create(text=variant) for variant in test["variants"]
    ]
    question.variants.set(variants)
    if test["variants"][test["answer"]] == variants[test["answer"]].text:
        question.answers.set([variants[test["answer"]]])
    else:
        print(test["question"])
    question.save()
    print(question)
# pprint(tests)