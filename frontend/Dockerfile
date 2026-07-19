FROM node:20-slim

WORKDIR /workspace

COPY package*.json /workspace/

RUN npm install

COPY . /workspace/

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
