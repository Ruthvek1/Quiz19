import os
import hashlib
from PIL import Image, ImageDraw, ImageFont
import textwrap
from datetime import datetime

class ImageService:
    def __init__(self, images_dir=None):
        if images_dir is None:
            # Use absolute path relative to the main.py file
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.images_dir = os.path.join(base_dir, 'static', 'images')
        else:
            self.images_dir = images_dir
        self.ensure_images_directory()
        
        # Default settings
        self.default_width = 800
        self.default_height = 600
        self.padding = 40
        self.line_spacing = 10
        self.background_color = (255, 255, 255)  # White
        self.text_color = (33, 37, 41)  # Dark gray
        self.watermark_color = (200, 200, 200, 100)  # Light gray with transparency
        
        # Font settings
        self.font_sizes = {
            'question': 24,
            'option': 20,
            'watermark': 14
        }
        
    def ensure_images_directory(self):
        """Ensure the images directory exists"""
        os.makedirs(self.images_dir, exist_ok=True)
        
    def get_font(self, size):
        """Get font with fallback to default"""
        try:
            # Try to use a system font
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
        except:
            try:
                # Fallback to another common font
                return ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", size)
            except:
                # Use default font as last resort
                return ImageFont.load_default()
    
    def calculate_text_dimensions(self, text, font, max_width):
        """Calculate the dimensions needed for wrapped text"""
        lines = textwrap.wrap(text, width=max_width // (font.size // 2))
        
        # Calculate total height
        total_height = 0
        max_line_width = 0
        
        for line in lines:
            bbox = font.getbbox(line)
            line_width = bbox[2] - bbox[0]
            line_height = bbox[3] - bbox[1]
            
            max_line_width = max(max_line_width, line_width)
            total_height += line_height + self.line_spacing
        
        return max_line_width, total_height, lines
    
    def draw_wrapped_text(self, draw, text, font, x, y, max_width, color):
        """Draw wrapped text and return the final y position"""
        lines = textwrap.wrap(text, width=max_width // (font.size // 2))
        current_y = y
        
        for line in lines:
            draw.text((x, current_y), line, font=font, fill=color)
            bbox = font.getbbox(line)
            line_height = bbox[3] - bbox[1]
            current_y += line_height + self.line_spacing
        
        return current_y
    
    def add_watermark(self, draw, width, height):
        """Add watermark to the image"""
        watermark_text = f"Quiz Platform - {datetime.now().strftime('%Y-%m-%d')}"
        watermark_font = self.get_font(self.font_sizes['watermark'])
        
        # Position watermark at bottom right
        bbox = watermark_font.getbbox(watermark_text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = width - text_width - 20
        y = height - text_height - 20
        
        draw.text((x, y), watermark_text, font=watermark_font, fill=self.watermark_color)
    
    def generate_question_image(self, question_text, question_id):
        """Generate an image for a question"""
        font = self.get_font(self.font_sizes['question'])
        max_text_width = self.default_width - (2 * self.padding)
        
        # Calculate required dimensions
        text_width, text_height, lines = self.calculate_text_dimensions(
            question_text, font, max_text_width
        )
        
        # Calculate image dimensions
        image_height = max(self.default_height, text_height + (2 * self.padding) + 100)
        
        # Create image
        image = Image.new('RGB', (self.default_width, image_height), self.background_color)
        draw = ImageDraw.Draw(image)
        
        # Add title
        title_font = self.get_font(self.font_sizes['question'] + 4)
        title_text = f"Question {question_id}"
        draw.text((self.padding, self.padding), title_text, font=title_font, fill=self.text_color)
        
        # Add question text
        title_bbox = title_font.getbbox(title_text)
        title_height = title_bbox[3] - title_bbox[1]
        question_y = self.padding + title_height + 30
        
        self.draw_wrapped_text(
            draw, question_text, font, 
            self.padding, question_y, 
            max_text_width, self.text_color
        )
        
        # Add watermark
        self.add_watermark(draw, self.default_width, image_height)
        
        # Generate filename
        text_hash = hashlib.md5(question_text.encode()).hexdigest()[:8]
        filename = f"question_{question_id}_{text_hash}.png"
        filepath = os.path.join(self.images_dir, filename)
        
        # Save image
        image.save(filepath, 'PNG', quality=95)
        
        return filename
    
    def generate_options_image(self, options, question_id):
        """Generate an image for question options"""
        font = self.get_font(self.font_sizes['option'])
        max_text_width = self.default_width - (2 * self.padding) - 60  # Space for option labels
        
        # Calculate total height needed
        total_height = self.padding * 2
        option_heights = []
        
        for key, option_text in options.items():
            _, text_height, _ = self.calculate_text_dimensions(
                option_text, font, max_text_width
            )
            option_heights.append(text_height)
            total_height += text_height + 40  # Space between options
        
        # Create image
        image_height = max(self.default_height, total_height + 100)
        image = Image.new('RGB', (self.default_width, image_height), self.background_color)
        draw = ImageDraw.Draw(image)
        
        # Add title
        title_font = self.get_font(self.font_sizes['option'] + 4)
        title_text = "Choose the correct answer:"
        draw.text((self.padding, self.padding), title_text, font=title_font, fill=self.text_color)
        
        # Add options
        title_bbox = title_font.getbbox(title_text)
        title_height = title_bbox[3] - title_bbox[1]
        current_y = self.padding + title_height + 30
        
        option_labels = ['A', 'B', 'C', 'D']
        for i, (key, option_text) in enumerate(options.items()):
            # Draw option label (A, B, C, D)
            label_font = self.get_font(self.font_sizes['option'] + 2)
            label = f"{option_labels[i]}."
            draw.text((self.padding, current_y), label, font=label_font, fill=self.text_color)
            
            # Draw option text
            option_x = self.padding + 50
            final_y = self.draw_wrapped_text(
                draw, option_text, font,
                option_x, current_y,
                max_text_width, self.text_color
            )
            
            current_y = final_y + 20  # Space between options
        
        # Add watermark
        self.add_watermark(draw, self.default_width, image_height)
        
        # Generate filename
        options_text = ''.join(options.values())
        text_hash = hashlib.md5(options_text.encode()).hexdigest()[:8]
        filename = f"options_{question_id}_{text_hash}.png"
        filepath = os.path.join(self.images_dir, filename)
        
        # Save image
        image.save(filepath, 'PNG', quality=95)
        
        return filename
    
    def generate_question_images(self, question):
        """Generate both question and options images for a question"""
        question_image = None
        options_image = None
        
        try:
            # Generate question image
            question_image = self.generate_question_image(
                question.question_text, 
                question.id
            )
            
            # Generate options image
            options = question.get_options()
            options_image = self.generate_options_image(
                options, 
                question.id
            )
            
            return {
                'question_image': question_image,
                'options_image': options_image,
                'success': True
            }
            
        except Exception as e:
            return {
                'question_image': question_image,
                'options_image': options_image,
                'success': False,
                'error': str(e)
            }
    
    def delete_question_images(self, question):
        """Delete existing images for a question"""
        try:
            if question.question_image_path:
                filepath = os.path.join(self.images_dir, question.question_image_path)
                if os.path.exists(filepath):
                    os.remove(filepath)
            
            if question.options_image_path:
                filepath = os.path.join(self.images_dir, question.options_image_path)
                if os.path.exists(filepath):
                    os.remove(filepath)
                    
            return True
        except Exception as e:
            print(f"Error deleting images: {e}")
            return False
    
    def get_image_url(self, filename):
        """Get the URL for accessing an image"""
        if filename:
            return f"/api/images/{filename}"
        return None

