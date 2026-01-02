from agents import Agent, Runner, function_tool
from agents import ItemHelpers
import asyncio
from dotenv import load_dotenv
load_dotenv()


spanish_agent = Agent(
    name= "spanish_agent",
    instructions= "You translate the user's message to spanish",
)


translation_pciker = Agent(
    name = "translation_picker",
    instructions="You pick the best spanish translation  from the given options"
)




async def main():
    msg = "hello my name is Dhruv Panchal. Write this in creative way in spanish."
    
    try:
        ## all are running in parallel
        res_1, res_2, res_3 = await asyncio.wait_for(
                        asyncio.gather(
                        Runner.run(
                            spanish_agent,
                            msg
                        ),
                        Runner.run(
                            spanish_agent,
                            msg
                        ),
                        Runner.run(
                            spanish_agent,
                            msg
                        ),
                        return_exceptions = True
                        ),
                        timeout=1.0  #### max seconds
            )
        
        print(res_1.final_output)
        print(res_2.final_output)
        print(res_3.final_output)
        

    except asyncio.TimeoutError:
        print("it took too long")    
    
    
    # res_1 = None
    # res_2 = None
    # res_3 = None
    
    # tasks = [
    #     asyncio.create_task(Runner.run(spanish_agent, msg)),
    #     asyncio.create_task(Runner.run(spanish_agent, msg)),
    #     asyncio.create_task(Runner.run(spanish_agent, msg)),
        
    # ]
    
    # for cor in asyncio.as_completed(tasks):
    #     result = await cor
    #     print(result)
    #     print(result.final_output)
    #     print("\n\n")
    
    # print(res_1, res_2, res_3)
    
    # outputs = [
    #     ItemHelpers.text_message_outputs(res_1.new_items),
    #     ItemHelpers.text_message_outputs(res_2.new_items),
    #     ItemHelpers.text_message_outputs(res_3.new_items),
        
    # ]
    
    # translation = "\n\n".join(outputs)
    
    # # print(translation)
    
    # best_translation = await Runner.run(
    #     translation_pciker,
    #     f"input{msg} \n\n Translations: \n {translation}",
    # )
    
    
    # print(f"Best Translation: {best_translation.final_output}")
    
    
if __name__ == "__main__":
    asyncio.run(main())



