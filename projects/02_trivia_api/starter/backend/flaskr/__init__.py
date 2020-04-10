import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)

  CORS(app, resources={r"*/*": {"origins": "*"}})

  @app.after_request
  def after_request(response):
      response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
      response.headers.add('Access-Control-Allow-Methods', 'GET, POST, DELETE')
      return response

  def paginate(selection, page):
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions
  '''
  @TODO: 
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route('/categories', methods=['GET'])
  def get_categories():
    try:
        categories = Category.query.all()
        if categories > 0:
          category_formatted = [category.format() for category in categories]
          result = {
            "status_code" : 200,
            "success" : True,
            "category": categories
          }
          return jsonify(result)
        abort(404)
    except:
        abort(422)

  '''
  @TODO: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''
  @app.route("/questions", methods=['GET'])
  def get_questions():
    try:
        page = int(request.args.get('page', 1))
        categories = list(map(Category.format, Category.query.all()))
        questions = Question.query.all()
        questions_query = paginate(questions, page)
        if len(questions_query) > 0:
            result = {
                "status_code" : 200,
                "success" : True,
                "questions": questions_query,
                "total_questions": len(questions_query),
                "categories": categories,
                "current_category": None,
            }
            return jsonify(result)
        abort(404)
    except:
        abort(422)

  '''
  @TODO: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
      try:
        question = Question.query.filter_by(id==question_id).delete()
        db.session.commit()
        result = {
          "status_code" : 200,
          "success" : True,
          "question" : question
        }
        return jsonify(result)
      except:
        db.session.rollback()
        abort(422)
      finally:
        db.session.close()
      return None

  '''
  @TODO: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''
  @app.route('/questions', methods=['POST'])
  def add_question():
    try:
        question = request.args.get('question')
        answer_text = request.args.get('answer_text')
        category = request.args.get('category')
        difficulty = int(request.args.get('difficulty'))
        id = len(Question.query.all()) + 1
        question = Question(question=question, answer=answer_text, category=category, difficulty=difficulty, id=id)
        db.session.add(question)
        db.session.commit()
        questions_query = Question.query.all()
        result = {
            "status_code" : 200,
            "success" : True,
            "question" : question.format(),
            "total_questions" : len(questions_query),
            "current_category" : category
        }
        return jsonify(result)
    except:
        db.session.rollback()
        abort(422)
    finally:
        db.session.close()
    return None

  '''
  @TODO: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''
  @app.route("/questions/search/", methods=['GET'])
  def get_questions_substring():
    try:
        searchTerm = request.args.get('searchTerm')
        query_string = "%" + searchTerm + "%"
        questions = Question.query.filter(Question.question.ilike(query_string)).all()
        total_questions = len(Question.query.all())
        if len(questions) > 0:
            paginated_questions = paginate(questions)
            questions_formatting = [question.format() for question in paginated_questions]
            result = {
                "status_code" : 200,
                "success" : True,
                "question" : question,
                "total_questions" : total_questions,
                "current_category" : None
            }
            return result
        abort(404)
    except:
        abort(500)
  '''
  @TODO: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  @app.route('/categories/<int:category_id>/questions', methods=['GET'])
  def get_categories_questions(category_id):
    try:
        category = Category.query.filter_by(id==category_id).first()
        category_name = category.name
        questions = Question.query.filter_by(category==category_name).all()
        total_questions = len(Question.query.all())
        if questions > 0:
            paginated_questions = paginate(questions)
            result = {
                "status_code" : 200,
                "success" : True,
                "questions" : paginated_questions,
                "total_questions" : total_questions,
                "current_category" : category_id
            }
            return result
        abort(404)
    except:
        abort(422)

  '''
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
  @app.route('/play', methods=['POST'])
  def play():
    data = request.args.get('previous_questions')
    previous_questions = request.args.get('previous_questions')
    quiz_category = request.args.get('category')
    if quiz_category != "ALL":
        category_id = quiz_category['id']
    try:
        if category_id:
            questions = Question.query.filter(Question.category==quiz_category).all()
        else:
            questions = Question.query.all()
        available_questions = []
        for question in questions:
            if question not in previous_questions:
                available_questions.append(question)
        if available_questions != []:
            rand_question = questions[random.random(0,len(available_questions)-1)]
            return jsonify({
                "status_code" : 200,
                "success" : True,
                "question" : rand_question.format(),
                'previous_questions': previous_questions,
                'quiz_category': quiz_category
            })
        else:
            return jsonify({
              "status_code" : 200,
              "success" : True,
              'question': 'There are no more questions in this category. Try a different category.',
              'previous_questions': previous_questions,
              'quiz_category': quiz_category
            })
        abort(404)
    except:
        abort(422)

  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
        "success" : False,
        "error" : 404,
        "message" : "Page Not Found"
    }), 404

  @app.errorhandler(422)
  def not_found(error):
    return jsonify({
      "success" : False,
      "error" : 422,
      "message" : "Unprocessable Entity"
    }), 422

  @app.errorhandler(500)
  def not_found(error):
    return jsonify({
      "success" : False,
      "error" : 500,
      "message" : "Internal Server Error"
    }), 500


  return app

    