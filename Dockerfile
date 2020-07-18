# Copyright Ⓒ 2020 "Sberbank Real Estate Center" Limited Liability Company. Licensed under the MIT license.
# Please, see the LICENSE.md file in project's root for full licensing information.
FROM python:3.8-slim

# Copy all necessary files
COPY ./ /app/
WORKDIR /app/

# Install python requirements
RUN pip3 install -U pip && pip3 install --no-cache-dir -r requirements.txt
