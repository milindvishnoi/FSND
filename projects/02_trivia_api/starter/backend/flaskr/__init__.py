import os
from flask import Flask, request, abort, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category, db

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)

  CORS(app, resources={r"*": {"origins": "*"}})

  @app.after_request
  def after_request(response):
      response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
      response.headers.add('Access-Control-Allow-Methods', 'GET, POST, DELETE')
      return response

  def paginate(selection, page):
    """
    This function is used to get the required questions per page.
    By just changing the QUESTIONS_PER_PAGE variable will change
    the number of questions you get per page
    """
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions

  @app.route('/categories', methods=['GET'])
  def get_categories():
    """
    As the name suggests the function returns the categories in our database
    """
    try:
        categories = Category.query.all()
        # To check if the category query returns something or not
        if len(categories) > 0:
          category_formatted = {category.id: category.type for category in categories}
          result = {
            "success" : True,
            "categories": category_formatted
          }
          return jsonify(result)
        abort(404)
    except:
        abort(422)

  @app.route("/questions", methods=['GET'])
  def get_questions():
    """
    Returns the questions from the database
    """
    try:
        page = int(request.args.get('page', 1))
        categories = Category.query.all()
        category_formatted = {category.id: category.type for category in categories}
        questions = Question.query.all()
        total_questions = len(questions)
        questions_query = paginate(questions, page)
        if len(questions_query) > 0:
            result = {
                "success": True,
                "questions": questions_query,
                "total_questions": total_questions,
                "categories": category_formatted,
                "current_category": None
            }
            return jsonify(result)
        abort(404)
    except:
        abort(422)

  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
      """
      Used to delete a specified question. The question is identified by it's id.
      """
      try:
        q = Question.query.filter_by(id=question_id)
        q = q.format()
        question = Question.query.filter_by(id=question_id).delete()
        db.session.commit()
        result = {
          "success": True,
          "question": q
        }
        return jsonify(result)
      except:
        db.session.rollback()
        abort(422)
      finally:
        db.session.close()
      return None

  @app.route('/questions', methods=['POST'])
  def add_question():
    """
    Used to create a new question
    """
    try:
        # Gets all the fields required for making Question
        request_json = request.get_json()
        question = request_json['question']
        answer_text = request_json['answer']
        category = request_json['category']
        difficulty = int(request_json['difficulty'])
        id = int(len(Question.query.all()) + 1)
        question = Question(id=id, question=question, answer=answer_text, category=category, difficulty=difficulty)
        # adding the question created into the database
        db.session.add(question)
        db.session.commit()
        questions_query = Question.query.all()
        result = {
            "success" : True,
            "question" : question.format(),
            "total_questions" : len(questions_query),
            "current_category" : category
        }
        return jsonify(result)
    except:
        # if there is a error
        db.session.rollback()
        abort(422)
    finally:
        db.session.close()
    return None

  @app.route("/questions/search", methods=['POST'])
  def get_questions_substring():
    """
    Checks if the given phrase is in any Question table's question column in database
    """
    try:
        data = request.get_json()
        search_term = data['searchTerm']
        query_string = "%" + search_term + "%"
        # checks if searchTerm exists in the the Questions table
        questions = Question.query.filter(Question.question.ilike(query_string)).all()
        total_questions = len(Question.query.all())
        categories = Category.query.all()
        category_formatted = {category.id: category.type for category in categories}
        page = int(request.args.get('page', 1))
        paginated_questions = paginate(questions, page)
        if len(paginated_questions)!= 0:
            result = {
                "success" : "True",
                "questions": paginated_questions,
                "total_questions": total_questions,
                "categories": category_formatted,
                "current_category": None
            }
            return jsonify(result)
        else:
            abort(404)
    except:
        abort(422)

  @app.route('/categories/<int:category_id>/questions', methods=['GET'])
  def get_categories_questions(category_id):
    """
    Gets all the question from a given category
    """
    try:
        category_id = str(category_id)
        page = int(request.args.get('page', 1))
        questions = Question.query.filter_by(category=category_id).all()
        total_questions = len(Question.query.all())
        if len(questions) > 0:
            paginated_questions = paginate(questions, page)
            result = {
                "success" : True,
                "questions" : paginated_questions,
                "total_questions" : total_questions,
                "current_category" : category_id
            }
            return jsonify(result)
        abort(404)
    except:
        abort(422)

  @app.route('/play', methods=['POST'])
  def play():
    """
    Used to start the game
    """
    data = request.get_json()
    previous_questions = data['previous_questions']
    quiz_category = data['quiz_category']
    category_id = 0
    if quiz_category != "ALL":
        category_id = int(quiz_category['id'])
    try:
        # Checking if quiz_category is "ALL" or not to set the questions variable by getting the
        # questions from database
        if category_id != 0:
            questions = Question.query.filter_by(category=category_id).all()
        else:
            questions = Question.query.all()
        available_questions = []
        # To get the questions that are not already used
        for question in questions:
            if question not in previous_questions:
                available_questions.append(question)
        if len(available_questions) > 0:
            # randomly selects a questions from available_questions
            rand_question = available_questions[random.randint(0,len(available_questions)-1)]
            return jsonify({
                "success" : True,
                "question" : rand_question.format(),
                "previous_questions" : previous_questions,
                'quiz_category': quiz_category
            })
        else:
            return jsonify({
              "success" : True,
              'question': 'There are no more questions in this category. Try another category!',
              "previous_questions" : previous_questions,
              'quiz_category': quiz_category
            })
        abort(404)
    except:
        abort(422)

  @app.errorhandler(404)
  def page_not_found(error):
    """
    To handle 404 error
    """
    return jsonify({
        "success": False,
        "error": 404,
        "message": "Page Not Found"
    }), 404

  @app.errorhandler(422)
  def unprocessable_entity(error):
    """
    To handle 422 error
    """
    return jsonify({
      "success": False,
      "error": 422,
      "message": "Unprocessable Entity"
    }), 422

  return app

