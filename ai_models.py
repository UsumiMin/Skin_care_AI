import google.generativeai as genai
import json
import os
import asyncio

genai.configure(api_key="AIzaSyBd77njV451Td_k5ncchyWiqtsoMXMsSwI")


class AiModel:
    __generation_config__ = {  #Настройки для работы ИИ
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "application/json"
    }
    
    def __init__(self, instruction_filename, model_name="gemini-1.5-flash",):
        
        with open(f"{instruction_filename}",encoding='UTF-8') as instruction_file:
            system_instruction = instruction_file.read()

        self.model = genai.GenerativeModel(
            model_name = model_name,
            generation_config = self.__generation_config__,
            system_instruction = system_instruction
        )


class VisionModel(AiModel):
    __instruction_filename__ = "skin_mod.txt"
    
    def __init__(self):

        AiModel.__init__(self, self.__instruction_filename__)

    async def proc_img(self, myfile, prompt = "") -> str:
        result = await self.model.generate_content_async(
            [myfile, "\n\n", prompt]
        )
        return result.text

    async def get_description(self, photo_filename, prompt = ""):
        myfile = genai.upload_file(photo_filename)
        response = await self.proc_img(myfile,prompt)
        return response


async def process_message():
    prompt = "Проанализируй мою кожу по этой фотографии и дай рекомендации по уходу. \n\n "
    response = await VisionModel.get_description(self=VisionModel(),photo_filename='IMG_20250419_151247_614.jpg', prompt=prompt)
    json_response = json.loads(response)
    print(json_response)
    return json_response['skin']

async def main():
    respons = await process_message()
    item_type = respons[0]['skin_type']
    print(item_type)
    problems = respons[1]['problems']
    print(problems)
    recomendation = respons[2]['recomendation']
    print(recomendation)


if __name__ == "__main__":
    asyncio.run(main())
