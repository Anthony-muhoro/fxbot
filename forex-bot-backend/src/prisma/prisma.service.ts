import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';
import { Pool } from 'pg';
import { PrismaPg } from '@prisma/adapter-pg';

@Injectable()
export class PrismaService
  extends PrismaClient
  implements OnModuleInit, OnModuleDestroy
{
  constructor() {
    // 1. Grab the URL loaded by your NestJS ConfigModule
    const connectionString = process.env.DATABASE_URL;

    // Safety check to prevent silent failures
    if (!connectionString) {
      throw new Error('DATABASE_URL is missing! Please check your .env file.');
    }

    // 2. Initialize the native Postgres connection pool
    const pool = new Pool({ connectionString });

    // 3. Bind the pool to the Prisma 7 Adapter
    const adapter = new PrismaPg(pool);

    // 4. Pass the configured adapter to the parent PrismaClient class
    super({ adapter });
  }

  async onModuleInit() {
    await this.$connect();
    console.log('PostgreSQL Database connected successfully');
  }

  async onModuleDestroy() {
    await this.$disconnect();
  }
}
