import os
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from src.models.user import db, Question
from src.routes.user import token_required, admin_required
from src.services.image_service import ImageService

image_bp = Blueprint('image', __name__)

# Initialize image service
image_service = ImageService()

@image_bp.route('/images/<filename>', methods=['GET'])
def serve_image(filename):
    """Serve generated images"""
    try:
        images_dir = image_service.images_dir
        return send_from_directory(images_dir, filename)
    except Exception as e:
        return jsonify({'success': False, 'error': {'message': 'Image not found'}}), 404

@image_bp.route('/images/question', methods=['POST'])
@token_required
@admin_required
def generate_question_image(current_user):
    """Generate image for a question"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': {'message': 'No data provided'}}), 400
        
        question_text = data.get('question_text')
        question_id = data.get('question_id', 'preview')
        
        if not question_text:
            return jsonify({'success': False, 'error': {'message': 'Question text is required'}}), 400
        
        # Generate question image
        filename = image_service.generate_question_image(question_text, question_id)
        image_url = image_service.get_image_url(filename)
        
        return jsonify({
            'success': True,
            'data': {
                'filename': filename,
                'url': image_url
            },
            'message': 'Question image generated successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

@image_bp.route('/images/options', methods=['POST'])
@token_required
@admin_required
def generate_options_image(current_user):
    """Generate image for question options"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': {'message': 'No data provided'}}), 400
        
        options = data.get('options')
        question_id = data.get('question_id', 'preview')
        
        if not options or not isinstance(options, dict):
            return jsonify({'success': False, 'error': {'message': 'Options are required'}}), 400
        
        # Validate options format
        required_keys = ['a', 'b', 'c', 'd']
        if not all(key in options for key in required_keys):
            return jsonify({'success': False, 'error': {'message': 'Options must include a, b, c, d'}}), 400
        
        # Generate options image
        filename = image_service.generate_options_image(options, question_id)
        image_url = image_service.get_image_url(filename)
        
        return jsonify({
            'success': True,
            'data': {
                'filename': filename,
                'url': image_url
            },
            'message': 'Options image generated successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

@image_bp.route('/questions/<int:question_id>/generate-images', methods=['POST'])
@token_required
@admin_required
def generate_question_images(current_user, question_id):
    """Generate both question and options images for a specific question"""
    try:
        question = Question.query.get_or_404(question_id)
        
        # Delete existing images if they exist
        image_service.delete_question_images(question)
        
        # Generate new images
        result = image_service.generate_question_images(question)
        
        if result['success']:
            # Update question with new image paths
            question.question_image_path = result['question_image']
            question.options_image_path = result['options_image']
            db.session.commit()
            
            return jsonify({
                'success': True,
                'data': {
                    'question_image': {
                        'filename': result['question_image'],
                        'url': image_service.get_image_url(result['question_image'])
                    },
                    'options_image': {
                        'filename': result['options_image'],
                        'url': image_service.get_image_url(result['options_image'])
                    }
                },
                'message': 'Images generated successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': {'message': result.get('error', 'Failed to generate images')}
            }), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

@image_bp.route('/quizzes/<int:quiz_id>/generate-all-images', methods=['POST'])
@token_required
@admin_required
def generate_all_quiz_images(current_user, quiz_id):
    """Generate images for all questions in a quiz"""
    try:
        questions = Question.query.filter_by(quiz_id=quiz_id).all()
        
        if not questions:
            return jsonify({'success': False, 'error': {'message': 'No questions found for this quiz'}}), 404
        
        results = []
        errors = []
        
        for question in questions:
            try:
                # Delete existing images
                image_service.delete_question_images(question)
                
                # Generate new images
                result = image_service.generate_question_images(question)
                
                if result['success']:
                    # Update question with new image paths
                    question.question_image_path = result['question_image']
                    question.options_image_path = result['options_image']
                    
                    results.append({
                        'question_id': question.id,
                        'question_image': result['question_image'],
                        'options_image': result['options_image']
                    })
                else:
                    errors.append({
                        'question_id': question.id,
                        'error': result.get('error', 'Unknown error')
                    })
                    
            except Exception as e:
                errors.append({
                    'question_id': question.id,
                    'error': str(e)
                })
        
        # Commit all successful updates
        if results:
            db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'generated': len(results),
                'errors': len(errors),
                'results': results,
                'error_details': errors
            },
            'message': f'Generated images for {len(results)} questions'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

@image_bp.route('/questions/<int:question_id>/images', methods=['GET'])
@token_required
def get_question_images(current_user, question_id):
    """Get image URLs for a question"""
    try:
        question = Question.query.get_or_404(question_id)
        
        # Check if user has access to this question
        # For now, allow access if user is taking the quiz or is admin
        if current_user.role != 'admin':
            # Additional access control can be added here
            pass
        
        return jsonify({
            'success': True,
            'data': {
                'question_image': image_service.get_image_url(question.question_image_path),
                'options_image': image_service.get_image_url(question.options_image_path)
            },
            'message': 'Question images retrieved'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

@image_bp.route('/images/preview', methods=['POST'])
@token_required
@admin_required
def preview_images(current_user):
    """Generate preview images for question and options"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': {'message': 'No data provided'}}), 400
        
        question_text = data.get('question_text')
        options = data.get('options')
        
        if not question_text or not options:
            return jsonify({'success': False, 'error': {'message': 'Question text and options are required'}}), 400
        
        results = {}
        
        # Generate question image preview
        if question_text:
            question_filename = image_service.generate_question_image(question_text, 'preview')
            results['question_image'] = {
                'filename': question_filename,
                'url': image_service.get_image_url(question_filename)
            }
        
        # Generate options image preview
        if options and isinstance(options, dict):
            options_filename = image_service.generate_options_image(options, 'preview')
            results['options_image'] = {
                'filename': options_filename,
                'url': image_service.get_image_url(options_filename)
            }
        
        return jsonify({
            'success': True,
            'data': results,
            'message': 'Preview images generated successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

