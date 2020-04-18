import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgresql://postgres:1{}/{}".format('@localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

    def tearDown(self):
        """Executed after reach test"""
        pass

    def test_get_categories(self):
        res = self.client().get('/categories')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['categories'])

    def test_get_questions(self):
        res = self.client().get('/questions?page=1')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'], True)
        self.assertTrue(data['questions'])
        self.assertTrue(data['total_questions'])
        self.assertTrue(data['categories'])
        self.assertEqual(data['current_category'], None)

    def test_add_question(self):
        res = self.client().post('/questions', json={"question": "NewQ?",
                                                     "answer": "answer_text",
                                                     "category": 1,
                                                     "difficulty": 1})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertTrue(data['question'])
        self.assertTrue(data['total_questions'])

    def test_delete_question(self):
        question = Question.query.first()
        res = self.client().delete('/questions/'+str(question.id))
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertTrue(data['question'])

    def test_get_questions_substring(self):
        res = self.client().post('/questions/search', json={"searchTerm": "?"})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertTrue(data['questions'])
        self.assertTrue(data['total_questions'])
        self.assertEqual(data['current_category'], None)

    def test_get_categories_questions(self):
        res = self.client().get('/categories/1/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertTrue(data['questions'])
        self.assertTrue(data['total_questions'])
        self.assertTrue(data['current_category'])

    def test_play(self):
        res = self.client().post('/play', json={"previous_questions": [],
                                                "quiz_category":
                                                {"type": "click", "id": 0}})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertTrue(data['question'])
        self.assertTrue(data['quiz_category'])

    def test_404_error(self):
        res = self.client().get('/questions?page=1000')
        data = json.loads(res.data)

        self.assertEqual(data['error'], 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], "Page Not Found")

    def test_422_error(self):
        res = self.client().get('/questions?page=x')
        data = json.loads(res.data)

        self.assertEqual(data['error'], 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], "Unprocessable Entity")


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
