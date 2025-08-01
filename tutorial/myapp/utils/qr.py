from myapp.views.forms import *
from myapp.utils.utils import *
from myapp.utils.decorators import *
from myapp.models import *
from myapp.views.helpers import *
from myapp.utils.sqlite_connector import * 
from django.conf import settings
from PIL import Image
import os
import re
import qrcode
import qrcode.image.svg
import qrcode.constants
try:
    from qrcode.image.styledpil import StyledPilImage
    STYLED_PIL_AVAILABLE = True
except ImportError:
    STYLED_PIL_AVAILABLE = False
import io
import base64
import xml.etree.ElementTree as ET




def process_logo_for_qr(logo_file=None):
    """
    Process logo image and convert to base64 for embedding in SVG
    """
    try:
        if logo_file:
            # Handle uploaded custom logo
            image = Image.open(logo_file)
        else:
            # Use default DataSpark icon - try multiple possible paths
            possible_paths = [
                os.path.join(settings.BASE_DIR, 'tutorial', 'static', 'DataSpark_Icon_582px.png'),
                os.path.join(settings.BASE_DIR, 'tutorial', 'myapp', 'staticfiles', 'DataSpark_Icon_582px.png'),
                os.path.join(settings.BASE_DIR, 'static', 'DataSpark_Icon_582px.png'),
            ]
            
            image = None
            for path in possible_paths:
                if os.path.exists(path):
                    image = Image.open(path)
                    break
            
            if image is None:
                return None
        
        # Convert to RGBA if not already
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Resize to appropriate size for QR code center (max 64x64)
        max_size = 64
        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Convert to base64
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return {
            'data': img_base64,
            'width': image.width,
            'height': image.height
        }
    except Exception as e:
        return None



def generate_qr_svg(content, logo_info=None, qr_color='#0066cc', background_color='#ffffff', shape_type='square', use_white_bg=False, frame_type='none', frame_color='#000000'):
    """
    Generate QR code SVG with logo and custom styling
    This function should always return a valid SVG unless there's a critical error
    """
    try:
        # Ensure content is not empty
        if not content or not content.strip():
            content = "DataSpark QR Code"  # Default content
        
        # Ensure colors are not None
        if qr_color is None:
            qr_color = '#000000'
        if background_color is None:
            background_color = '#ffffff'
        if frame_color is None:
            frame_color = '#000000'
        
        # If no logo_info provided and we want DataSpark logo, try to get it
        if logo_info is None:
            # Don't automatically load DataSpark logo - respect the user's choice
            pass
        
        # Determine if background should be transparent
        use_transparent_bg = not use_white_bg
        
        # Create QR code with SVG factory for square shapes
        factory = qrcode.image.svg.SvgPathImage
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H if logo_info else qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
            image_factory=factory
        )
        
        qr.add_data(content)
        qr.make(fit=True)
        
        # Generate SVG
        svg_img = qr.make_image(fill_color=qr_color)
        
        # Get SVG content as string
        svg_buffer = io.BytesIO()
        svg_img.save(svg_buffer)
        svg_content = svg_buffer.getvalue().decode('utf-8')
        
        # Parse SVG to customize and add logo
        root = ET.fromstring(svg_content)
        
        # Handle background color
        if use_transparent_bg:
            # Remove any background rectangles to make it transparent
            for rect in root.findall('.//{http://www.w3.org/2000/svg}rect'):
                if rect.get('fill') == 'white' or rect.get('fill') == '#ffffff':
                    root.remove(rect)
            
            # Also handle path-based backgrounds but preserve QR code color
            for path in root.findall('.//{http://www.w3.org/2000/svg}path'):
                if path.get('fill') == 'white' or path.get('fill') == '#ffffff':
                    path.set('fill', 'none')
                # Ensure QR code paths keep the correct color
                elif path.get('fill') != qr_color and path.get('fill') not in ['none', 'transparent']:
                    path.set('fill', qr_color)
        else:
            # Set white background color
            svg_ns = 'http://www.w3.org/2000/svg'
            ET.register_namespace('', svg_ns)
            
            # Get SVG dimensions
            viewbox = root.get('viewBox')
            if viewbox:
                vb_parts = viewbox.split()
                if len(vb_parts) >= 4:
                    vb_x, vb_y, width, height = map(float, vb_parts)
                else:
                    vb_x, vb_y, width, height = 0, 0, 100, 100
            else:
                vb_x, vb_y, width, height = 0, 0, 100, 100
            
            # Add white background rectangle
            bg_rect = ET.Element(f'{{{svg_ns}}}rect')
            bg_rect.set('x', str(vb_x))
            bg_rect.set('y', str(vb_y))
            bg_rect.set('width', str(width))
            bg_rect.set('height', str(height))
            bg_rect.set('fill', '#ffffff')
            root.insert(0, bg_rect)  # Insert at beginning
            
            # Ensure QR code paths have the correct color
            for path in root.findall('.//{http://www.w3.org/2000/svg}path'):
                if path.get('fill') and path.get('fill') not in ['white', '#ffffff', 'none', 'transparent']:
                    path.set('fill', qr_color)
        
        # Add frame if requested
        if frame_type != 'none':
            add_frame_to_svg(root, frame_type, frame_color)
        
        # Add logo if provided
        if logo_info:
            add_logo_to_svg(root, logo_info)
        
        # Convert back to string with proper SVG declaration
        svg_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        svg_content += ET.tostring(root, encoding='unicode', method='xml')
        
        # Fix SVG namespace issues that can cause rendering problems
        svg_content = svg_content.replace('svg:svg', 'svg')
        svg_content = svg_content.replace('svg:path', 'path')
        svg_content = svg_content.replace('svg:rect', 'rect')
        svg_content = svg_content.replace('svg:image', 'image')
        svg_content = svg_content.replace('xmlns:svg="http://www.w3.org/2000/svg"', 'xmlns="http://www.w3.org/2000/svg"')
        
        # Enhanced namespace cleanup to handle both svg: and ns0: prefixes
        svg_content = svg_content.replace('ns0:svg', 'svg')
        svg_content = svg_content.replace('ns0:path', 'path')
        svg_content = svg_content.replace('ns0:rect', 'rect')
        svg_content = svg_content.replace('ns0:image', 'image')
        svg_content = svg_content.replace('xmlns:ns0="http://www.w3.org/2000/svg"', 'xmlns="http://www.w3.org/2000/svg"')
        
        return svg_content
        
    except Exception as e:
        # Create a minimal fallback QR code
        try:
            # Ensure content exists
            if not content or not content.strip():
                content = "DataSpark QR Code"
            
            # Create minimal QR code as fallback
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=4,
                image_factory=qrcode.image.svg.SvgPathImage
            )
            qr.add_data(content)
            qr.make(fit=True)
            
            svg_img = qr.make_image(fill_color='#000000')
            svg_buffer = io.BytesIO()
            svg_img.save(svg_buffer)
            fallback_content = svg_buffer.getvalue().decode('utf-8')
            
            # Add proper SVG declaration
            fallback_svg = '<?xml version="1.0" encoding="UTF-8"?>\n' + fallback_content
            
            # Fix SVG namespace issues that can cause rendering problems
            fallback_svg = fallback_svg.replace('svg:svg', 'svg')
            fallback_svg = fallback_svg.replace('svg:path', 'path')
            fallback_svg = fallback_svg.replace('svg:rect', 'rect')
            fallback_svg = fallback_svg.replace('svg:image', 'image')
            fallback_svg = fallback_svg.replace('xmlns:svg="http://www.w3.org/2000/svg"', 'xmlns="http://www.w3.org/2000/svg"')
            
            # Enhanced namespace cleanup to handle both svg: and ns0: prefixes
            fallback_svg = fallback_svg.replace('ns0:svg', 'svg')
            fallback_svg = fallback_svg.replace('ns0:path', 'path')
            fallback_svg = fallback_svg.replace('ns0:rect', 'rect')
            fallback_svg = fallback_svg.replace('ns0:image', 'image')
            fallback_svg = fallback_svg.replace('xmlns:ns0="http://www.w3.org/2000/svg"', 'xmlns="http://www.w3.org/2000/svg"')
            
            return fallback_svg
            
        except Exception as e2:
            return None


def generate_rounded_qr_svg(qr, qr_color, use_white_bg, frame_type, frame_color, logo_info):
    """
    Generate SVG for rounded QR code with proper color and logo support
    """
    try:
        svg_ns = 'http://www.w3.org/2000/svg'
        
        # Get QR code matrix
        matrix = qr.get_matrix()
        border = qr.border
        box_size = qr.box_size
        
        # Calculate dimensions
        modules_count = len(matrix)
        total_width = (modules_count + 2 * border) * box_size
        total_height = total_width
        
        # Create SVG root element
        svg_root = ET.Element(f'{{{svg_ns}}}svg')
        svg_root.set('xmlns', svg_ns)
        svg_root.set('width', str(total_width))
        svg_root.set('height', str(total_height))
        svg_root.set('viewBox', f'0 0 {total_width} {total_height}')
        
        # Add background if white background is requested
        if use_white_bg:
            bg_rect = ET.Element(f'{{{svg_ns}}}rect')
            bg_rect.set('x', '0')
            bg_rect.set('y', '0')
            bg_rect.set('width', str(total_width))
            bg_rect.set('height', str(total_height))
            bg_rect.set('fill', '#ffffff')
            svg_root.append(bg_rect)
        
        # Create connected shapes with rounded outer edges
        # First, create paths for connected components
        visited = [[False for _ in range(modules_count)] for _ in range(modules_count)]
        
        def get_connected_component(start_row, start_col):
            """Get all connected dark modules starting from given position"""
            if (start_row < 0 or start_row >= modules_count or 
                start_col < 0 or start_col >= modules_count or
                visited[start_row][start_col] or not matrix[start_row][start_col]):
                return set()
            
            component = set()
            stack = [(start_row, start_col)]
            
            while stack:
                row, col = stack.pop()
                if (row < 0 or row >= modules_count or 
                    col < 0 or col >= modules_count or
                    visited[row][col] or not matrix[row][col]):
                    continue
                
                visited[row][col] = True
                component.add((row, col))
                
                # Add 4-connected neighbors
                for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    stack.append((row + dr, col + dc))
            
            return component
        
        # Find all connected components
        components = []
        for row in range(modules_count):
            for col in range(modules_count):
                if matrix[row][col] and not visited[row][col]:
                    component = get_connected_component(row, col)
                    if component:
                        components.append(component)
        
        # Create SVG paths for each component with rounded corners
        corner_radius = box_size * 0.25
        
        for component in components:
            # Create a path that outlines the component
            path_data = create_rounded_path_for_component(component, box_size, border, corner_radius)
            
            if path_data:
                path_elem = ET.Element(f'{{{svg_ns}}}path')
                path_elem.set('d', path_data)
                path_elem.set('fill', qr_color)
                path_elem.set('fill-rule', 'evenodd')
                svg_root.append(path_elem)
        
        # Add frame if requested
        if frame_type != 'none':
            add_frame_to_svg(svg_root, frame_type, frame_color)
        
        # Note: Logos are not supported for rounded QR codes to maintain the rounded aesthetic
        
        # Convert to string
        svg_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        svg_content += ET.tostring(svg_root, encoding='unicode', method='xml')
        
        # Fix SVG namespace issues that can cause rendering problems
        # Handle both svg: and ns0: prefixes
        svg_content = svg_content.replace('svg:svg', 'svg')
        svg_content = svg_content.replace('svg:path', 'path')
        svg_content = svg_content.replace('svg:rect', 'rect')
        svg_content = svg_content.replace('svg:image', 'image')
        svg_content = svg_content.replace('ns0:svg', 'svg')
        svg_content = svg_content.replace('ns0:path', 'path')
        svg_content = svg_content.replace('ns0:rect', 'rect')
        svg_content = svg_content.replace('ns0:image', 'image')
        svg_content = svg_content.replace('xmlns:svg="http://www.w3.org/2000/svg"', 'xmlns="http://www.w3.org/2000/svg"')
        svg_content = svg_content.replace('xmlns:ns0="http://www.w3.org/2000/svg"', '')
        
        return svg_content
        
    except Exception as e:
        return None




def convert_pil_to_svg(pil_img, logo_info, qr_color, background_color, shape_type, frame_type, frame_color):
    """
    This function is kept for compatibility but should not be used for rounded QR codes
    """
    return convert_pil_to_svg_fallback(pil_img, logo_info, qr_color, background_color, shape_type, frame_type, frame_color)


def convert_pil_to_svg_fallback(pil_img, logo_info, qr_color, background_color, shape_type, frame_type, frame_color):
    """
    Fallback method: Convert PIL image to SVG format as bitmap with overlays
    """
    try:
        # Convert PIL to base64 and embed in SVG
        buffer = io.BytesIO()
        pil_img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # Create SVG wrapper with frame support
        width, height = pil_img.size
        svg_ns = 'http://www.w3.org/2000/svg'
        
        # Create SVG root element
        svg_root = ET.Element(f'{{{svg_ns}}}svg')
        svg_root.set('xmlns', svg_ns)
        svg_root.set('width', str(width))
        svg_root.set('height', str(height))
        svg_root.set('viewBox', f'0 0 {width} {height}')
        
        # Add the QR code image
        image_elem = ET.Element(f'{{{svg_ns}}}image')
        image_elem.set('x', '0')
        image_elem.set('y', '0')
        image_elem.set('width', str(width))
        image_elem.set('height', str(height))
        image_elem.set('href', f'data:image/png;base64,{img_base64}')
        svg_root.append(image_elem)
        
        # Add frame if requested
        if frame_type != 'none':
            add_frame_to_svg(svg_root, frame_type, frame_color)
        
        # Add logo if provided (this will work even with bitmap background)
        if logo_info:
            add_logo_to_svg(svg_root, logo_info)
        
        # Convert to string
        svg_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        svg_content += ET.tostring(svg_root, encoding='unicode', method='xml')
        
        return svg_content
    except Exception as e:
        return None


def add_frame_to_svg(root, frame_type, frame_color='#000000'):
    """
    Add a frame around the QR code SVG
    """
    try:
        # Ensure frame_color is not None
        if frame_color is None:
            frame_color = '#000000'
            
        svg_ns = 'http://www.w3.org/2000/svg'
        ET.register_namespace('', svg_ns)
        
        # Get SVG dimensions
        viewbox = root.get('viewBox')
        if viewbox:
            vb_parts = viewbox.split()
            if len(vb_parts) >= 4:
                vb_x, vb_y, width, height = map(float, vb_parts)
            else:
                vb_x, vb_y, width, height = 0, 0, 100, 100
        else:
            vb_x, vb_y, width, height = 0, 0, 100, 100
        
        # Frame settings
        frame_width = min(width, height) * 0.02  # 2% of the smallest dimension
        
        if frame_type == 'simple':
            # Simple rectangular frame
            frame_rect = ET.Element(f'{{{svg_ns}}}rect')
            frame_rect.set('x', str(vb_x))
            frame_rect.set('y', str(vb_y))
            frame_rect.set('width', str(width))
            frame_rect.set('height', str(height))
            frame_rect.set('fill', 'none')
            frame_rect.set('stroke', frame_color)
            frame_rect.set('stroke-width', str(frame_width))
            root.append(frame_rect)
            
        elif frame_type == 'rounded':
            # Rounded rectangular frame
            corner_radius = frame_width * 3
            frame_rect = ET.Element(f'{{{svg_ns}}}rect')
            frame_rect.set('x', str(vb_x + frame_width/2))
            frame_rect.set('y', str(vb_y + frame_width/2))
            frame_rect.set('width', str(width - frame_width))
            frame_rect.set('height', str(height - frame_width))
            frame_rect.set('rx', str(corner_radius))
            frame_rect.set('ry', str(corner_radius))
            frame_rect.set('fill', 'none')
            frame_rect.set('stroke', frame_color)
            frame_rect.set('stroke-width', str(frame_width))
            root.append(frame_rect)
            
    except Exception as e:
        pass


def add_logo_to_svg(root, logo_info):
    """
    Add logo to the center of the SVG QR code
    """
    try:
        # Get SVG dimensions from viewBox
        viewbox = root.get('viewBox')
        if viewbox:
            vb_parts = viewbox.split()
            if len(vb_parts) >= 4:
                width = float(vb_parts[2])
                height = float(vb_parts[3])
            else:
                width = height = 100
        else:
            # Try to get from width/height attributes
            width_attr = root.get('width', '100')
            height_attr = root.get('height', '100')
            width = float(width_attr.replace('mm', '').replace('px', '').replace('pt', ''))
            height = float(height_attr.replace('mm', '').replace('px', '').replace('pt', ''))
        
        # Calculate center position
        center_x = width / 2
        center_y = height / 2
        logo_size = min(width, height) * 0.12  # Logo is 12% of QR code size
        
        # Add namespace for proper SVG handling
        svg_ns = 'http://www.w3.org/2000/svg'
        ET.register_namespace('', svg_ns)
        
        # Add white background circle for logo
        circle = ET.Element(f'{{{svg_ns}}}circle')
        circle.set('cx', str(center_x))
        circle.set('cy', str(center_y))
        circle.set('r', str(logo_size * 1.4))
        circle.set('fill', 'white')
        root.append(circle)
        
        if logo_info and logo_info.get('data'):
            # Use uploaded or default DataSpark image
            image_elem = ET.Element(f'{{{svg_ns}}}image')
            image_elem.set('x', str(center_x - logo_size))
            image_elem.set('y', str(center_y - logo_size))
            image_elem.set('width', str(logo_size * 2))
            image_elem.set('height', str(logo_size * 2))
            image_elem.set('href', f"data:image/png;base64,{logo_info['data']}")
            image_elem.set('preserveAspectRatio', 'xMidYMid meet')
            root.append(image_elem)
        else:
            # Fallback to geometric logo
            logo_group = ET.Element(f'{{{svg_ns}}}g')
            logo_group.set('transform', f'translate({center_x},{center_y})')
            
            # Add a stylized diamond shape for "DataSpark"
            diamond = ET.Element(f'{{{svg_ns}}}polygon')
            diamond_size = logo_size * 0.7
            points = f"{-diamond_size*0.5},0 0,{-diamond_size*0.5} {diamond_size*0.5},0 0,{diamond_size*0.5}"
            diamond.set('points', points)
            diamond.set('fill', '#0066cc')
            logo_group.append(diamond)
            
            # Add inner spark symbol
            spark = ET.Element(f'{{{svg_ns}}}polygon')
            spark_size = diamond_size * 0.35
            spark_points = f"{-spark_size*0.3},{-spark_size*0.1} {-spark_size*0.1},{-spark_size*0.3} {spark_size*0.1},{-spark_size*0.1} {spark_size*0.3},{-spark_size*0.3} {spark_size*0.1},{spark_size*0.1} {spark_size*0.3},{spark_size*0.3} {spark_size*0.1},{spark_size*0.1} {-spark_size*0.1},{spark_size*0.3} {-spark_size*0.3},{spark_size*0.1} {-spark_size*0.1},{-spark_size*0.1}"
            spark.set('points', spark_points)
            spark.set('fill', 'white')
            logo_group.append(spark)
            
            root.append(logo_group)
            
    except Exception as e:
        pass


def create_rounded_path_for_component(component, box_size, border, corner_radius):
    """Create a rounded SVG path for a connected component"""
    if not component:
        return ""
    
    # Convert component to grid coordinates
    min_row = min(pos[0] for pos in component)
    max_row = max(pos[0] for pos in component)
    min_col = min(pos[1] for pos in component)
    max_col = max(pos[1] for pos in component)
    
    # Create a grid to mark which cells are filled
    grid_height = max_row - min_row + 1
    grid_width = max_col - min_col + 1
    grid = [[False for _ in range(grid_width)] for _ in range(grid_height)]
    
    for row, col in component:
        grid[row - min_row][col - min_col] = True
    
    # Check if this is a simple rectangle
    is_rectangle = all(grid[r][c] for r in range(grid_height) for c in range(grid_width))
    
    if is_rectangle:
        # For rectangles, create a simple rounded rectangle
        x = (min_col + border) * box_size
        y = (min_row + border) * box_size
        width = grid_width * box_size
        height = grid_height * box_size
        
        # Adjust corner radius to not exceed half the smallest dimension
        actual_radius = min(corner_radius, min(width, height) / 2)
        
        # Create rounded rectangle path
        path_data = f"M {x + actual_radius} {y} "
        path_data += f"L {x + width - actual_radius} {y} "
        path_data += f"Q {x + width} {y} {x + width} {y + actual_radius} "
        path_data += f"L {x + width} {y + height - actual_radius} "
        path_data += f"Q {x + width} {y + height} {x + width - actual_radius} {y + height} "
        path_data += f"L {x + actual_radius} {y + height} "
        path_data += f"Q {x} {y + height} {x} {y + height - actual_radius} "
        path_data += f"L {x} {y + actual_radius} "
        path_data += f"Q {x} {y} {x + actual_radius} {y} Z"
        
        return path_data
    else:
        # For complex shapes, trace the outer contour and create a rounded path
        return create_contour_path(grid, min_row, min_col, box_size, border, corner_radius, component)


def create_contour_path(grid, min_row, min_col, box_size, border, corner_radius, component):
    """Create a contour path around a complex shape with rounded corners"""
    grid_height = len(grid)
    grid_width = len(grid[0]) if grid_height > 0 else 0
    
    if grid_height == 0 or grid_width == 0:
        return ""
    
    # Simple approach: create individual rounded rectangles but merge them visually
    # by using a smaller corner radius to maintain connectivity
    paths = []
    small_radius = corner_radius * 0.3  # Much smaller radius to maintain shape integrity
    
    for row in range(grid_height):
        for col in range(grid_width):
            if grid[row][col]:
                # Check if this cell is on the border (has at least one empty neighbor)
                is_border = False
                actual_row = row + min_row
                actual_col = col + min_col
                
                # Check 8-connected neighbors
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = actual_row + dr, actual_col + dc
                        if (nr, nc) not in component:
                            is_border = True
                            break
                    if is_border:
                        break
                
                # Only add rounded rectangles for border cells
                if is_border:
                    x = (actual_col + border) * box_size
                    y = (actual_row + border) * box_size
                    
                    path_data = f"M {x + small_radius} {y} "
                    path_data += f"L {x + box_size - small_radius} {y} "
                    path_data += f"Q {x + box_size} {y} {x + box_size} {y + small_radius} "
                    path_data += f"L {x + box_size} {y + box_size - small_radius} "
                    path_data += f"Q {x + box_size} {y + box_size} {x + box_size - small_radius} {y + box_size} "
                    path_data += f"L {x + small_radius} {y + box_size} "
                    path_data += f"Q {x} {y + box_size} {x} {y + box_size - small_radius} "
                    path_data += f"L {x} {y + small_radius} "
                    path_data += f"Q {x} {y} {x + small_radius} {y} Z "
                    
                    paths.append(path_data)
                else:
                    # For interior cells, create simple rectangles
                    x = (actual_col + border) * box_size
                    y = (actual_row + border) * box_size
                    
                    path_data = f"M {x} {y} "
                    path_data += f"L {x + box_size} {y} "
                    path_data += f"L {x + box_size} {y + box_size} "
                    path_data += f"L {x} {y + box_size} Z "
                    
                    paths.append(path_data)
    
    return " ".join(paths)

