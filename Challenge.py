# Challenge model

class Challenge:
    def get_attributes():
        return ['title', 'category', 'url', 'remaining_score', 'score_max', 'remaining_questions', 'questions_count', 'difficulty', 'tags']

    def __init__(self, url, title=None, category=None, remaining_score=None, questions_count=None, remaining_questions=None, score_max=None, difficulty=None, tags=None):
        self.url = url
        self.title = title
        self.category = category
        self.remaining_score = remaining_score
        self.questions_count = questions_count
        self.remaining_questions = remaining_questions
        self.score_max = score_max
        self.difficulty = difficulty
        self.tags = tags

    def get_dict(self):
        return {
            'url': self.url,
            'title': self.title,
            'category': self.category,
            'remaining_score': self.remaining_score,
            'questions_count': self.questions_count,
            'remaining_questions': self.remaining_questions,
            'score_max': self.score_max,
            'difficulty': self.difficulty,
            'tags': self.tags
        }