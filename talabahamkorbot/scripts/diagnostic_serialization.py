import asyncio
import os
import sys
import json
from datetime import datetime

# Add the project root to sys.path
sys.path.append("/home/user/talabahamkor/talabahamkorbot")

from database.db_connect import AsyncSessionLocal
from database.models import Student, Election, ElectionCandidate, ElectionVote
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from api.schemas import ElectionDetailSchema, ElectionCandidateSchema

async def test_serialization():
    async with AsyncSessionLocal() as session:
        election_id = 6
        student_id = 730
        
        print(f"--- Testing Pydantic Serialization for Election {election_id} ---")
        
        student = await session.get(Student, student_id)
        
        try:
            election = await session.scalar(
                select(Election)
                .where(and_(Election.id == election_id))
                .options(
                    selectinload(Election.candidates).selectinload(ElectionCandidate.student),
                    selectinload(Election.candidates).selectinload(ElectionCandidate.faculty)
                )
            )
            
            voted = await session.scalar(
                select(ElectionVote).where(
                    and_(
                        ElectionVote.election_id == election_id,
                        ElectionVote.voter_id == student.id
                    )
                )
            )

            # Convert to schema (Replicating logic from election.py)
            candidate_schemas = []
            for cand in election.candidates:
                candidate_schemas.append(ElectionCandidateSchema(
                    id=cand.id,
                    full_name=cand.student.full_name if cand.student else "Ismsiz nomzod",
                    faculty_name=cand.faculty.name if cand.faculty else "Noma'lum fakultet",
                    campaign_text=cand.campaign_text,
                    image_url=cand.photo_id,
                    order=cand.order
                ))

            detail = ElectionDetailSchema(
                id=election.id,
                title=election.title,
                description=election.description,
                deadline=election.deadline,
                has_voted=voted is not None,
                voted_candidate_id=voted.candidate_id if voted else None,
                candidates=candidate_schemas
            )
            
            print("Successfully created ElectionDetailSchema object.")
            print("JSON Output:")
            # Using model_dump_json for Pydantic v2
            try:
                print(detail.model_dump_json(indent=2))
            except AttributeError:
                # Fallback for Pydantic v1
                print(detail.json(indent=2))
                
            print("\n--- Serialization SUCCESS ---")
        except Exception as e:
            import traceback
            print(f"\n--- Serialization FAILED ---")
            print(f"Error: {e}")
            print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_serialization())
