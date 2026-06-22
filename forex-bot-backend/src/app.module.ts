import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { PrismaModule } from './prisma/prisma.module';
import { ConfigModule } from '@nestjs/config/dist/config.module';
import { RedisModule } from './redis/redis.module';

@Module({
  imports: [ConfigModule.forRoot({ isGlobal: true }), PrismaModule, RedisModule],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
