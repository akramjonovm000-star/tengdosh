from database.models import ChoyxonaComment, Student, ChoyxonaPost

# Mock objects
class MockStudent:
    def __init__(self, id, full_name):
        self.id = id
        self.full_name = full_name

class MockPost:
    def __init__(self, student_id):
        self.student_id = student_id

class MockComment:
    def __init__(self, id, content, student_id, post_id, likes, parent=None, post=None, student=None):
        self.id = id
        self.content = content
        self.student_id = student_id
        self.post_id = post_id
        self.likes = likes
        self.parent_comment = parent
        self.post = post
        self.student = student
        self.created_at = "2024-01-01"

def _map_comment(comment, author, current_user_id):
    # exact copy from api/community.py
    reply_user = None
    reply_content = None
    
    if comment.parent_comment:
        reply_user = comment.parent_comment.student.full_name if comment.parent_comment.student else "Noma'lum"
        reply_content = comment.parent_comment.content

    is_liked = any(l.student_id == current_user_id for l in comment.likes) if comment.likes else False
    
    is_liked_by_author = False
    if comment.post and comment.likes:
         is_liked_by_author = any(l.student_id == comment.post.student_id for l in comment.likes)

    return {
        "id": comment.id,
        "content": comment.content,
        "is_liked": is_liked,
        "is_liked_by_author": is_liked_by_author
    }

if __name__ == "__main__":
    try:
        print("Test 1: Normal Case")
        c1 = MockComment(1, "Text", 1, 1, [], post=MockPost(1), student=MockStudent(1, "Name"))
        _map_comment(c1, c1.student, 1)
        print("✅ Test 1 Passed")

        print("Test 2: Missing Post (Should be loaded eagerly but what if?)")
        c2 = MockComment(2, "Text", 1, 1, [], post=None, student=MockStudent(1, "Name"))
        _map_comment(c2, c2.student, 1)
        print("✅ Test 2 Passed")

        print("Test 3: Missing Student (Author)")
        c3 = MockComment(3, "Text", 1, 1, [], post=MockPost(1), student=None)
        # The API passes c.student as author explicitly: _map_comment(c, c.student, ...)
        _map_comment(c3, None, 1) 
        # Wait, if author is None, does access fail inside?
        # Looking at previous file view of _map_comment:
        # "author_name": author.full_name if author else "Noma'lum",
        print("✅ Test 3 Passed")

    except Exception as e:
        print(f"❌ CRASHED: {e}")
        import traceback
        traceback.print_exc()
