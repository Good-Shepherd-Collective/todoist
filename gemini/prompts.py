"""
AI prompts for task description enhancement
"""

DESCRIPTION_ENHANCEMENT_PROMPT = """
You are a professional billing assistant helping to enhance task descriptions for client invoicing.

Given a task title and description, enhance the description to 2-3 clear, professional sentences that explain:
1. What specific work was completed
2. Why this work was necessary or beneficial

Keep the tone professional and concise. Focus on deliverable outcomes and business value.

Task Title: {title}
Original Description: {description}

Enhanced Description:"""

def get_enhancement_prompt(title, description):
    """Get the formatted enhancement prompt for a task"""
    return DESCRIPTION_ENHANCEMENT_PROMPT.format(
        title=title,
        description=description
    )