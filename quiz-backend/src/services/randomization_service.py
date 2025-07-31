import random
import hashlib
from typing import List, Dict, Any

class RandomizationService:
    """Service for randomizing quiz questions and options to prevent cheating"""
    
    def __init__(self):
        pass
    
    def generate_user_seed(self, user_id: int, quiz_id: int) -> int:
        """Generate a consistent seed for a user-quiz combination"""
        # Create a consistent seed based on user and quiz IDs
        seed_string = f"{user_id}_{quiz_id}"
        hash_object = hashlib.md5(seed_string.encode())
        # Convert first 8 characters of hash to integer
        return int(hash_object.hexdigest()[:8], 16)
    
    def randomize_questions(self, questions: List[Dict[Any, Any]], user_id: int, quiz_id: int) -> List[Dict[Any, Any]]:
        """Randomize the order of questions for a specific user"""
        if not questions:
            return questions
        
        # Use consistent seed for this user-quiz combination
        seed = self.generate_user_seed(user_id, quiz_id)
        random.seed(seed)
        
        # Create a copy and shuffle
        randomized_questions = questions.copy()
        random.shuffle(randomized_questions)
        
        # Update question order for tracking
        for i, question in enumerate(randomized_questions):
            question['randomized_order'] = i
        
        return randomized_questions
    
    def randomize_options(self, question: Dict[Any, Any], user_id: int, quiz_id: int) -> Dict[Any, Any]:
        """Randomize the order of options for a specific question and user"""
        if not question or 'options' not in question:
            return question
        
        # Use consistent seed based on user, quiz, and question
        seed_string = f"{user_id}_{quiz_id}_{question.get('id', 0)}"
        hash_object = hashlib.md5(seed_string.encode())
        seed = int(hash_object.hexdigest()[:8], 16)
        random.seed(seed)
        
        # Get original options
        original_options = question['options']
        option_keys = ['a', 'b', 'c', 'd']
        
        # Create list of (key, value) pairs
        option_pairs = [(key, original_options.get(key, '')) for key in option_keys if original_options.get(key)]
        
        # Shuffle the values while keeping track of the mapping
        option_values = [pair[1] for pair in option_pairs]
        random.shuffle(option_values)
        
        # Create new options mapping
        new_options = {}
        correct_answer_mapping = {}
        
        for i, key in enumerate(option_keys[:len(option_values)]):
            new_options[key] = option_values[i]
            # Find which original key had this value
            for orig_key, orig_value in option_pairs:
                if orig_value == option_values[i]:
                    correct_answer_mapping[orig_key] = key
                    break
        
        # Update the question
        randomized_question = question.copy()
        randomized_question['options'] = new_options
        
        # Update correct answer mapping
        if 'correct_answer' in question:
            original_correct = question['correct_answer']
            randomized_question['correct_answer'] = correct_answer_mapping.get(original_correct, original_correct)
        
        # Store the mapping for answer verification
        randomized_question['option_mapping'] = correct_answer_mapping
        
        return randomized_question
    
    def get_randomized_quiz(self, quiz_data: Dict[Any, Any], user_id: int) -> Dict[Any, Any]:
        """Get a fully randomized quiz for a specific user"""
        if not quiz_data or 'questions' not in quiz_data:
            return quiz_data
        
        quiz_id = quiz_data.get('id', 0)
        randomized_quiz = quiz_data.copy()
        
        # Randomize questions if enabled
        if quiz_data.get('randomize_questions', False):
            randomized_quiz['questions'] = self.randomize_questions(
                quiz_data['questions'], user_id, quiz_id
            )
        
        # Randomize options if enabled
        if quiz_data.get('randomize_options', False):
            for i, question in enumerate(randomized_quiz['questions']):
                randomized_quiz['questions'][i] = self.randomize_options(
                    question, user_id, quiz_id
                )
        
        return randomized_quiz
    
    def verify_answer(self, question: Dict[Any, Any], user_answer: str, original_correct: str) -> bool:
        """Verify if the user's answer is correct, accounting for randomization"""
        # If there's an option mapping, use it to translate the answer
        if 'option_mapping' in question:
            option_mapping = question['option_mapping']
            # Reverse the mapping to find original answer
            reverse_mapping = {v: k for k, v in option_mapping.items()}
            original_user_answer = reverse_mapping.get(user_answer, user_answer)
            return original_user_answer == original_correct
        
        # No randomization, direct comparison
        return user_answer == original_correct
    
    def get_question_mapping(self, user_id: int, quiz_id: int, question_id: int) -> Dict[str, str]:
        """Get the option mapping for a specific question and user"""
        # This would typically be stored in the database for the session
        # For now, we'll regenerate it (consistent due to seeding)
        seed_string = f"{user_id}_{quiz_id}_{question_id}"
        hash_object = hashlib.md5(seed_string.encode())
        seed = int(hash_object.hexdigest()[:8], 16)
        random.seed(seed)
        
        option_keys = ['a', 'b', 'c', 'd']
        shuffled_keys = option_keys.copy()
        random.shuffle(shuffled_keys)
        
        # Create mapping from original to randomized
        mapping = {}
        for i, original_key in enumerate(option_keys):
            mapping[original_key] = shuffled_keys[i]
        
        return mapping

