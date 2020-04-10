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

        question = Question(id=1, question="What's your name?", difficulty=1, category="KnowYou", answer="milind")
        category = Category(id=1, type="KnowYou")
        self.db.session.add(question)
        self.db.session.add(category)
        self.db.session.commit()


    
    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    TODO
    Write at least one test for each test for successful operation and for expected errors.
    """
    def test_get_categories():
        res = self.client().get('/categories')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['category'])

     def test_get_questions():
        res = self.client().get('/questions?page=1')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['questions'])
        self.assertTrue(data['total_questions'])
        self.assertTrue(data['categories'])
        self.assertTrue(data['current_category'])

    def test_add_questions():
        res = self.client().post('/questions', json={"question": "NewQ",
                                                        "answer_text": "answer_text",
                                                        "category" : "KnowYou",
                                                        "difficulty": 1})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['questions'])
        self.assertTrue(data['total_questions'])
        self.assertTrue(data['current_category'])

    def test_delete_question():
        res = self.client().delete('/questions/2')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['questions'])

    def test_get_questions_substring():
        res = self.client().post('/question/search/a')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['questions'])
        self.assertTrue(data['total_questions'])
        self.assertTrue(data['current_category'])



    def test_get_categories_questions():
        res = self.client().post('/categories/1/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['questions'])
        self.assertTrue(data['total_questions'])
        self.assertTrue(data['current_category'])

    def test_play():
        res = self.client().post('/play', json={"previous_questions": [],
                                            "category": "ALL"})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['questions'])
        self.assertTrue(data['previous_question'])
        self.assertTrue(data['quiz_category'])

    def test_404_error():
        res = self.client().get('/questions?page=1000')
        data = json.loads(res.data)

        self.assertEqual(res.error, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], "Page Not Found")

    def test_422_error():
        res = self.client().get('/questions')
        data = json.loads(res.data)

        self.assertEqual(res.error, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], "Unprocessable Entity")

    def test_500_error():
        res = self.client().post('/questions/search/a')
        data = json.loads(res.data)

        self.assertEqual(res.error, 500)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], "Internal Server Error")

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()