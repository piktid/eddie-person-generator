<p align="center">
  <img src="https://studio.piktid.com/logo.svg" alt="SuperID by PiktID logo" width="150">
  </br>
  <h3 align="center"><a href="[https://studio.piktid.com](https://studio.piktid.com)">Person Generator by PiktID</a></h3>
</p>


# Eddie - Person Generator 1.0.0
[![Official Website](https://img.shields.io/badge/Official%20Website-piktid.com-blue?style=flat&logo=world&logoColor=white)](https://piktid.com)
[![Discord Follow](https://dcbadge.vercel.app/api/server/FJU39e9Z4P?style=flat)](https://discord.com/invite/FJU39e9Z4P)

Eddie - Person Generator is a GenAI tool designed to generate variations of people in images based on different geographical locations.
It allows you to select a person in your photo and transform them to appear as if they were from another region of the world.

## About
Eddie utilizes generative AI to create authentic-looking variations of people in photos. It's particularly useful for:

- <ins>Location-based variations</ins>: Change how a person appears based on different geographical regions (Africa, Middle East, East Asia, etc.)
- <ins>Photo customization</ins>: Quickly generate region-specific variations of your images
- <ins>Content creation</ins>: Create diverse representation in your visual content

## Available Keywords

Eddie works by transforming people based on geographical regions. The following keywords are available:

```
- Africa
- Middle East
- East Asia
- North Europe
- South Europe
- North America
- South America
- Oceania
```

These keywords are defined in the `editPerson_dict.py` file and must be used exactly as written when making API calls.

## Getting Started

The following instructions suppose you have already installed a recent version of Python. To use any PiktID API, an access token is required.

> **Step 0** - Register <a href="https://studio.piktid.com">here</a>. 10 credits are given for free to all new users.

> **Step 1** - Clone the Eddie - Person Generator repository
```bash
# Installation commands
$ git clone https://github.com/piktid/eddie-person-generator.git
$ cd eddie-person-generator
```

> **Step 2** - Export your email and password as environmental variables
```bash
$ export EDDIE_EMAIL={Your email here}
$ export EDDIE_PASSWORD={Your password here}
```

> **Step 3** - Run the main function with a URL or local file path of the image and specify a keyword
```bash
# Using a URL with a keyword
$ python3 main.py --input_url 'your-url' --keyword 'Africa'

# Using a local file path with a keyword
$ python3 main.py --input_filepath '/path/to/your/image.jpg' --keyword 'North Europe'
```

You can customize the generation parameters with the following options:

```bash
# Generate a variation with specific parameters
$ python3 main.py --input_filepath '/path/to/your/image.jpg' --id_person 0 --keyword 'Middle East' --seed 12345 --output_filepath '/path/to/save/output.jpg'
```

## Available Parameters

- **input_url**: URL of the image to process
- **input_filepath**: Local path to the image file
- **output_filepath**: Where to save the generated image
- **id_person**: Index of the person to modify in the image (default: 0)
- **keyword**: Geographical location to use for variation (REQUIRED - see Available Keywords section)
- **seed**: Random seed for reproducible results (default: random)

## Contact
office@piktid.com
