import os
import sys

# Ensure src is in python path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from memory.memory_manager import MemoryManager

def main():
    print("--- Starting Native Memori Integration Test ---")
    
    try:
        manager = MemoryManager()
    except Exception as e:
        print(f"Initialization Error: {e}")
        return

    # Set context
    user_id = "user-test-native-002"
    process_id = "test-process-native"
    manager.set_context(user_id=user_id, process_id=process_id)
    
    client = manager.get_client()

    print(f"\n--- Conversation (User: {user_id}) ---")
    
    # 1. State a fact
    prompt_1 = "My favorite color is purple and I live in Tokyo."
    print(f"You: {prompt_1}")
    try:
        response1 = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt_1}
            ],
        )
        print(f"AI: {response1.choices[0].message.content}\n")
    except Exception as e:
        print(f"Error during chat completion: {e}")
        return

    # 2. Ask for recall
    prompt_2 = "What is my favorite color?"
    print(f"You: {prompt_2}")
    try:
        response2 = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt_2}],
        )
        print(f"AI: {response2.choices[0].message.content}\n")
    except Exception as e:
        print(f"Error during recall: {e}")

    print("\nWaiting for memory augmentation...")
    manager.wait_for_augmentation()
    print("Done.")

if __name__ == "__main__":
    main()
